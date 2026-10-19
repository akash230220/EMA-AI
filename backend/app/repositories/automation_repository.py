"""Repository layer for automation rules and their execution audit log."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from app.models.automation_rule import AutomationRuleModel, RuleExecutionLogModel
from app.repositories.base import BaseRepository


class AutomationRuleRepository(BaseRepository[AutomationRuleModel]):
    collection_name = "automation_rules"
    model_class = AutomationRuleModel

    async def list_for_user(
        self,
        user_id: str,
        *,
        enabled: bool | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[AutomationRuleModel], int]:
        filter_data: dict[str, Any] = {"user_id": user_id}
        if enabled is not None:
            filter_data["enabled"] = enabled

        total = await self.count_documents(filter_data)
        skip = (page - 1) * page_size
        results = await self.find_many(filter_data, skip=skip, limit=page_size, sort=[("priority", 1), ("created_at", -1)])
        return results, total

    async def toggle(self, rule_id: str, user_id: str, enabled: bool) -> AutomationRuleModel | None:
        now = datetime.now(timezone.utc)
        return await self.update_one(
            {"_id": rule_id, "user_id": user_id},
            {"$set": {"enabled": enabled, "updated_at": now}},
        )


class RuleExecutionLogRepository(BaseRepository[RuleExecutionLogModel]):
    collection_name = "rule_execution_logs"
    model_class = RuleExecutionLogModel

    async def list_for_user(self, user_id: str, *, page: int = 1, page_size: int = 20) -> tuple[list[RuleExecutionLogModel], int]:
        filter_data = {"user_id": user_id}
        total = await self.count_documents(filter_data)
        skip = (page - 1) * page_size
        results = await self.find_many(filter_data, skip=skip, limit=page_size, sort=[("executed_at", -1)])
        return results, total

    async def list_for_user_and_rule(
        self, user_id: str, rule_id: str, *, page: int = 1, page_size: int = 20
    ) -> tuple[list[RuleExecutionLogModel], int]:
        filter_data = {"user_id": user_id, "rule_id": rule_id}
        total = await self.count_documents(filter_data)
        skip = (page - 1) * page_size
        results = await self.find_many(filter_data, skip=skip, limit=page_size, sort=[("executed_at", -1)])
        return results, total


__all__ = ["AutomationRuleRepository", "RuleExecutionLogRepository"]
