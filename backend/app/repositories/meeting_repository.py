"""Repository for meetings and detected calendar events."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from app.models.meeting import MeetingModel
from app.repositories.base import BaseRepository


class MeetingRepository(BaseRepository[MeetingModel]):
    collection_name = "meetings"
    model_class = MeetingModel

    async def list_for_user(
        self,
        user_id: str,
        *,
        start: datetime | None = None,
        end: datetime | None = None,
        status: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[MeetingModel], int]:
        filter_data: dict[str, Any] = {"user_id": user_id}
        if start is not None:
            filter_data["start_time"] = {"$gte": start}
        if end is not None:
            filter_data["end_time"] = {"$lte": end}
        if status:
            filter_data["status"] = status

        total = await self.count_documents(filter_data)
        skip = (page - 1) * page_size
        results = await self.find_many(filter_data, skip=skip, limit=page_size, sort=[("start_time", 1)])
        return results, total

    async def confirm(self, meeting_id: str, user_id: str) -> MeetingModel | None:
        now = datetime.now(timezone.utc)
        return await self.update_one(
            {"_id": meeting_id, "user_id": user_id},
            {"$set": {"status": "confirmed", "updated_at": now}},
        )

    async def decline(self, meeting_id: str, user_id: str) -> MeetingModel | None:
        now = datetime.now(timezone.utc)
        return await self.update_one(
            {"_id": meeting_id, "user_id": user_id},
            {"$set": {"status": "declined", "updated_at": now}},
        )


__all__ = ["MeetingRepository"]
