"""Repository helpers for users and user sessions."""

from __future__ import annotations

from typing import Any

from bson import ObjectId

from app.models.user import SessionModel, UserModel
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository[UserModel]):
    collection_name = "users"
    model_class = UserModel

    async def get_by_google_sub(self, google_sub: str) -> UserModel | None:
        return await self.find_one({"google_sub": google_sub})

    async def get_by_email(self, email: str) -> UserModel | None:
        return await self.find_one({"email": email})

    async def exists(self, google_sub: str | None = None, email: str | None = None) -> bool:
        filter_data: dict[str, Any] = {}
        if google_sub is not None:
            filter_data["google_sub"] = google_sub
        if email is not None:
            filter_data["email"] = email
        return await self.count_documents(filter_data) > 0

    async def upsert_by_google_sub(self, user: UserModel) -> UserModel:
        existing_document = await self.collection.find_one({"google_sub": user.google_sub})
        if existing_document and not isinstance(existing_document.get("_id"), ObjectId):
            user.id = ObjectId()
            await self.collection.delete_one({"_id": existing_document["_id"]})
            return await self.insert_one(user)

        result = await self.collection.find_one_and_update(
            {"google_sub": user.google_sub},
            {"$set": self._model_to_doc(user)},
            upsert=True,
            return_document=True,
            sort=[("_id", 1)],
        )
        return self.model_class.model_validate(result)


class SessionRepository(BaseRepository[SessionModel]):
    collection_name = "sessions"
    model_class = SessionModel

    async def get_active_sessions_for_user(self, user_id: str) -> list[SessionModel]:
        return await self.find_many({"user_id": user_id, "revoked": False})

    async def revoke_session(self, session_id: str) -> bool:
        return await self.update_one({"_id": session_id}, {"$set": {"revoked": True}}) is not None


__all__ = ["UserRepository", "SessionRepository"]
