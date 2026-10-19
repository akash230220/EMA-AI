"""Repository for copilot conversations and message history."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from app.models.copilot import CopilotConversationModel, CopilotMessageModel
from app.repositories.base import BaseRepository


class CopilotConversationRepository(BaseRepository[CopilotConversationModel]):
    collection_name = "copilot_conversations"
    model_class = CopilotConversationModel

    async def list_for_user(self, user_id: str, *, page: int = 1, page_size: int = 20) -> tuple[list[CopilotConversationModel], int]:
        filter_data: dict[str, Any] = {"user_id": user_id}
        total = await self.count_documents(filter_data)
        skip = (page - 1) * page_size
        results = await self.find_many(filter_data, skip=skip, limit=page_size, sort=[("last_message_at", -1)])
        return results, total

    async def append_message(self, conversation_id: str, user_id: str, message: CopilotMessageModel) -> CopilotConversationModel | None:
        now = datetime.now(timezone.utc)
        return await self.update_one(
            {"_id": conversation_id, "user_id": user_id},
            {"$push": {"messages": self._model_to_doc(message)}, "$set": {"updated_at": now, "last_message_at": now}},
        )

    async def clear_messages(self, conversation_id: str, user_id: str) -> CopilotConversationModel | None:
        now = datetime.now(timezone.utc)
        return await self.update_one(
            {"_id": conversation_id, "user_id": user_id},
            {"$set": {"messages": [], "updated_at": now, "last_message_at": now}},
        )


__all__ = ["CopilotConversationRepository"]
