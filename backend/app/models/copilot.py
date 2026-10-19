# backend/app/models/copilot.py
"""
Copilot conversation + message documents. Not in the original Phase 1
list under models/ explicitly, but required by copilot_service.py
(referenced in the endpoints/copilot.py we generated) — grouped here
since it's a first-class feature with its own persistence needs.
"""

from datetime import datetime
from typing import Optional

from pydantic import Field

from app.models.base import MongoBaseModel, PyObjectId, utcnow


class CopilotToolCall(MongoBaseModel.__base__):
    model_config = {"populate_by_name": True}

    name: str
    label: Optional[str] = None
    input: Optional[dict] = None


class CopilotSource(MongoBaseModel.__base__):
    """A RAG citation — which email backed a claim in an assistant message."""

    model_config = {"populate_by_name": True}

    email_id: str
    snippet: str
    score: float


class CopilotMessageModel(MongoBaseModel.__base__):
    """Embedded within CopilotConversationModel.messages — not a top-level collection."""

    model_config = {"populate_by_name": True}

    id: str = Field(default_factory=lambda: str(__import__("uuid").uuid4()))
    role: str  # user | assistant
    content: str
    tool_calls: list[CopilotToolCall] = Field(default_factory=list)
    sources: list[CopilotSource] = Field(default_factory=list)
    feedback: Optional[str] = None  # up | down
    feedback_comment: Optional[str] = None
    created_at: datetime = Field(default_factory=utcnow)


class CopilotConversationModel(MongoBaseModel):
    """Collection: `copilot_conversations`"""

    user_id: PyObjectId
    title: str = "New conversation"
    messages: list[CopilotMessageModel] = Field(default_factory=list)

    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)
    last_message_at: datetime = Field(default_factory=utcnow)