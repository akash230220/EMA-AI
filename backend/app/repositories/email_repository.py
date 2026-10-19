"""Repository layer for email documents and search-driven data access."""

from __future__ import annotations

from typing import Any

from app.models.email import EmailModel
from app.repositories.base import BaseRepository


class EmailRepository(BaseRepository[EmailModel]):
    collection_name = "emails"
    model_class = EmailModel

    async def list_for_user(
        self,
        user_id: str,
        *,
        page: int = 1,
        page_size: int = 20,
        category: str | None = None,
        priority: str | None = None,
        intent: str | None = None,
        sentiment: str | None = None,
        unread_only: bool | None = None,
        pending_reply_only: bool | None = None,
        archived: bool | None = None,
        search: str | None = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
    ) -> tuple[list[EmailModel], int]:
        filter_data: dict[str, Any] = {"user_id": user_id}

        if category:
            filter_data["category"] = category
        if priority:
            filter_data["priority"] = priority
        if intent:
            filter_data["intent"] = intent
        if sentiment:
            filter_data["sentiment"] = sentiment
        if unread_only is not None:
            filter_data["is_read"] = not unread_only
        if pending_reply_only is not None:
            filter_data["pending_reply"] = pending_reply_only
        if archived is not None:
            filter_data["archived"] = archived
        if search:
            filter_data["$or"] = [
                {"subject": {"$regex": search, "$options": "i"}},
                {"sender_email": {"$regex": search, "$options": "i"}},
                {"snippet": {"$regex": search, "$options": "i"}},
            ]

        sort_direction = -1 if sort_order.lower() == "desc" else 1
        sort_spec = [(sort_by, sort_direction)]
        total = await self.count_documents(filter_data)
        skip = (page - 1) * page_size
        results = await self.find_many(filter_data, skip=skip, limit=page_size, sort=sort_spec)
        return results, total

    async def get_for_user(self, user_id: str, email_id: str) -> EmailModel | None:
        return await self.find_one({"user_id": user_id, "_id": email_id})

    async def mark_read(self, user_id: str, email_id: str, is_read: bool) -> EmailModel | None:
        return await self.update_one({"user_id": user_id, "_id": email_id}, {"$set": {"is_read": is_read, "updated_at": __import__("datetime").datetime.now(__import__("datetime").timezone.utc)}})

    async def mark_archived(self, user_id: str, email_id: str, archived: bool) -> EmailModel | None:
        return await self.update_one({"user_id": user_id, "_id": email_id}, {"$set": {"archived": archived, "updated_at": __import__("datetime").datetime.now(__import__("datetime").timezone.utc)}})

    async def soft_delete(self, user_id: str, email_id: str) -> bool:
        return await self.delete_one({"user_id": user_id, "_id": email_id})

    async def bulk_update(self, user_id: str, email_ids: list[str], action: str) -> int:
        filter_data = {"user_id": user_id, "_id": {"$in": email_ids}}
        update: dict[str, Any] = {"$set": {"updated_at": __import__("datetime").datetime.now(__import__("datetime").timezone.utc)}}
        if action == "mark_read":
            update["$set"]["is_read"] = True
        elif action == "mark_unread":
            update["$set"]["is_read"] = False
        elif action == "archive":
            update["$set"]["archived"] = True
        elif action == "unarchive":
            update["$set"]["archived"] = False
        elif action == "delete":
            result = await self.collection.delete_many(filter_data)
            return result.deleted_count
        else:
            return 0

        result = await self.collection.update_many(filter_data, update)
        return result.modified_count


__all__ = ["EmailRepository"]
