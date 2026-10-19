"""Repository for analytics snapshot aggregates."""

from __future__ import annotations

from datetime import date
from typing import Any

from app.models.analytics_snapshot import AnalyticsSnapshotModel
from app.repositories.base import BaseRepository


class AnalyticsSnapshotRepository(BaseRepository[AnalyticsSnapshotModel]):
    collection_name = "analytics_snapshots"
    model_class = AnalyticsSnapshotModel

    async def get_for_user_on_date(self, user_id: str, snapshot_date: date) -> AnalyticsSnapshotModel | None:
        return await self.find_one({"user_id": user_id, "snapshot_date": snapshot_date})

    async def list_for_user_range(self, user_id: str, start_date: date, end_date: date) -> list[AnalyticsSnapshotModel]:
        return await self.find_many(
            {"user_id": user_id, "snapshot_date": {"$gte": start_date, "$lte": end_date}},
            sort=[("snapshot_date", 1)],
        )

    async def upsert_daily_snapshot(self, snapshot: AnalyticsSnapshotModel) -> AnalyticsSnapshotModel:
        lookup = {"user_id": snapshot.user_id, "snapshot_date": snapshot.snapshot_date}
        result = await self.collection.find_one_and_update(
            lookup,
            {"$set": self._model_to_doc(snapshot)},
            upsert=True,
            return_document=True,
            sort=[("_id", 1)],
        )
        return self.model_class.model_validate(result)


__all__ = ["AnalyticsSnapshotRepository"]
