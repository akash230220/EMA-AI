# backend/app/models/base.py
"""
Shared base model + ObjectId handling for every Mongo document model.
Motor returns/accepts raw dicts with BSON ObjectId — this bridges
that with Pydantic v2's validation, so every model below can declare
`id: PyObjectId` and have it serialize to a plain string for JSON
API responses (matching every frontend type's `id: string` shape).
"""

from datetime import datetime, timezone
from typing import Annotated, Any

from bson import ObjectId
from pydantic import BaseModel, ConfigDict, Field, GetCoreSchemaHandler
from pydantic_core import core_schema


class _ObjectIdPydanticAnnotation:
    """
    Makes bson.ObjectId usable as a Pydantic v2 field type — validates
    incoming values (str or ObjectId) and serializes outgoing values
    to str, so API responses never leak raw ObjectId objects.
    """

    @classmethod
    def __get_pydantic_core_schema__(cls, _source_type: Any, _handler: GetCoreSchemaHandler) -> core_schema.CoreSchema:
        def validate(value: Any) -> ObjectId:
            if isinstance(value, ObjectId):
                return value
            if isinstance(value, str) and ObjectId.is_valid(value):
                return ObjectId(value)
            raise ValueError(f"Invalid ObjectId: {value!r}")

        return core_schema.json_or_python_schema(
            json_schema=core_schema.chain_schema(
                [core_schema.str_schema(), core_schema.no_info_plain_validator_function(validate)]
            ),
            python_schema=core_schema.union_schema(
                [
                    core_schema.is_instance_schema(ObjectId),
                    core_schema.chain_schema(
                        [core_schema.str_schema(), core_schema.no_info_plain_validator_function(validate)]
                    ),
                ]
            ),
            serialization=core_schema.plain_serializer_function_ser_schema(str),
        )


PyObjectId = Annotated[ObjectId, _ObjectIdPydanticAnnotation]


class MongoBaseModel(BaseModel):
    """
    Base class for every document model. `id` maps to Mongo's `_id`
    via alias, and `populate_by_name` allows constructing instances
    with either `id=` or `_id=` — Motor's find_one()/insert_one()
    results use `_id`, while our own code often wants to pass `id=`.
    """

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str},
    )

    id: PyObjectId = Field(default_factory=ObjectId, alias="_id")

    def to_mongo(self) -> dict:
        """Serializes to a dict suitable for Motor insert_one/update_one, keeping ObjectId as-is (not stringified)."""
        return _to_mongo_value(self)


def _to_mongo_value(value: Any) -> Any:
    if isinstance(value, ObjectId):
        return value
    if isinstance(value, BaseModel):
        result = {}
        for field_name, field_info in value.__class__.model_fields.items():
            field_value = getattr(value, field_name)
            if field_value is None:
                continue
            key = field_info.alias or field_name
            result[key] = _to_mongo_value(field_value)
        return result
    if isinstance(value, list):
        return [_to_mongo_value(item) for item in value]
    if isinstance(value, tuple):
        return tuple(_to_mongo_value(item) for item in value)
    if isinstance(value, dict):
        return {key: _to_mongo_value(item) for key, item in value.items()}
    return value


def utcnow() -> datetime:
    """Single source of truth for 'now' across every model's default timestamps — always UTC, always timezone-aware."""
    return datetime.now(timezone.utc)