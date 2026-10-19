"""Repository helpers for tasks extracted or created by the user."""

from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Any

from app.models.task import TaskModel
from app.repositories.base import BaseRepository


class TaskRepository(BaseRepository[TaskModel]):
    collection_name = "tasks"
    model_class = TaskModel

    async def list_for_user(
        self,
        user_id: str,
        *,
        status: str | None = None,
        priority: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[TaskModel], int]:
        filter_data: dict[str, Any] = {"user_id": user_id}
        if status:
            filter_data["status"] = status
        if priority:
            filter_data["priority"] = priority

        total = await self.count_documents(filter_data)
        skip = (page - 1) * page_size
        results = await self.find_many(filter_data, skip=skip, limit=page_size, sort=[("due_date", 1), ("created_at", -1)])
        return results, total

    async def get_by_email(self, user_id: str, email_id: str) -> list[TaskModel]:
        return await self.find_many({"user_id": user_id, "source_email_id": email_id})

    async def complete(self, task_id: str, user_id: str) -> TaskModel | None:
        now = datetime.now(timezone.utc)
        return await self.update_one(
            {"_id": task_id, "user_id": user_id},
            {"$set": {"status": "completed", "completed_at": now, "updated_at": now}},
        )

    async def reopen(self, task_id: str, user_id: str) -> TaskModel | None:
        now = datetime.now(timezone.utc)
        return await self.update_one(
            {"_id": task_id, "user_id": user_id},
            {"$set": {"status": "pending", "updated_at": now}},
        )


__all__ = ["TaskRepository"]
