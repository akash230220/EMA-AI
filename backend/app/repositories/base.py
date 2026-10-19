"""Shared repository primitives for Mongo-backed document models."""

from __future__ import annotations

from typing import Any, Generic, TypeVar

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorCollection, AsyncIOMotorDatabase
from pydantic import BaseModel

from app.db.mongo_client import get_database

T = TypeVar("T", bound=BaseModel)


class BaseRepository(Generic[T]):
    """Thin CRUD wrapper around a Mongo collection.

    The repository is intentionally generic so each domain-specific repository can
    delegate to the same set of helpers while keeping domain logic in the child
    classes.
    """

    collection_name: str
    model_class: type[T]

    def __init__(self, database: AsyncIOMotorDatabase | None = None, collection_name: str | None = None):
        self.database = database or get_database()
        self.collection_name = collection_name or self.collection_name
        self.collection: AsyncIOMotorCollection = self.database[self.collection_name]

    @staticmethod
    def _normalize_id(value: Any) -> ObjectId | None:
        if value is None:
            return None
        if isinstance(value, ObjectId):
            return value
        if isinstance(value, str):
            if ObjectId.is_valid(value):
                return ObjectId(value)
            return None
        return None

    @staticmethod
    def _normalize_filter(filter_data: dict[str, Any] | None) -> dict[str, Any]:
        if not filter_data:
            return {}
        normalized: dict[str, Any] = {}
        for key, value in filter_data.items():
            if key.endswith("_id") and isinstance(value, str):
                id_value = BaseRepository._normalize_id(value)
                normalized[key] = id_value if id_value is not None else value
            elif isinstance(value, dict):
                normalized[key] = BaseRepository._normalize_filter(value)
            else:
                normalized[key] = value
        return normalized

    def _model_to_doc(self, model: T) -> dict[str, Any]:
        return model.to_mongo()

    def _doc_to_model(self, document: dict[str, Any] | None) -> T | None:
        if document is None:
            return None
        return self.model_class.model_validate(document)

    async def insert_one(self, model: T, *, session: Any | None = None) -> T:
        document = self._model_to_doc(model)
        result = await self.collection.insert_one(document, session=session)
        document["_id"] = result.inserted_id
        return self.model_class.model_validate(document)

    async def insert_many(self, models: list[T], *, session: Any | None = None) -> list[T]:
        documents = [self._model_to_doc(model) for model in models]
        result = await self.collection.insert_many(documents, session=session)
        inserted_ids = list(result.inserted_ids.values())
        for i, doc in enumerate(documents):
            doc["_id"] = inserted_ids[i]
        return [self.model_class.model_validate(doc) for doc in documents]

    async def get_by_id(self, value: str | ObjectId, *, projection: dict[str, Any] | None = None) -> T | None:
        object_id = self._normalize_id(value)
        if object_id is None:
            return None
        document = await self.collection.find_one({"_id": object_id}, projection=projection)
        return self._doc_to_model(document)

    async def find_one(self, filter_data: dict[str, Any] | None = None, *, projection: dict[str, Any] | None = None, sort: list[tuple[str, int]] | None = None) -> T | None:
        cursor = self.collection.find_one(self._normalize_filter(filter_data), projection=projection, sort=sort)
        document = await cursor
        return self._doc_to_model(document)

    async def find_many(
        self,
        filter_data: dict[str, Any] | None = None,
        *,
        skip: int = 0,
        limit: int | None = None,
        sort: list[tuple[str, int]] | None = None,
        projection: dict[str, Any] | None = None,
    ) -> list[T]:
        cursor = self.collection.find(self._normalize_filter(filter_data), projection=projection).skip(skip)
        if sort:
            cursor = cursor.sort(sort)
        if limit is not None:
            cursor = cursor.limit(limit)
        documents = await cursor.to_list(length=limit if limit is not None else 1000)
        return [self.model_class.model_validate(document) for document in documents]

    async def count_documents(self, filter_data: dict[str, Any] | None = None) -> int:
        return await self.collection.count_documents(self._normalize_filter(filter_data))

    async def update_one(self, filter_data: dict[str, Any], update: dict[str, Any], *, upsert: bool = False) -> T | None:
        result = await self.collection.find_one_and_update(
            self._normalize_filter(filter_data),
            update,
            return_document=True,
            upsert=upsert,
            sort=[("_id", 1)],
        )
        return self._doc_to_model(result)

    async def replace_one(self, filter_data: dict[str, Any], replacement: T, *, upsert: bool = False) -> T | None:
        document = self._model_to_doc(replacement)
        result = await self.collection.find_one_and_replace(
            self._normalize_filter(filter_data),
            document,
            return_document=True,
            upsert=upsert,
            sort=[("_id", 1)],
        )
        return self._doc_to_model(result)

    async def delete_one(self, filter_data: dict[str, Any]) -> bool:
        result = await self.collection.delete_one(self._normalize_filter(filter_data))
        return result.deleted_count > 0

    async def delete_many(self, filter_data: dict[str, Any] | None = None) -> int:
        result = await self.collection.delete_many(self._normalize_filter(filter_data))
        return result.deleted_count


__all__ = ["BaseRepository"]
