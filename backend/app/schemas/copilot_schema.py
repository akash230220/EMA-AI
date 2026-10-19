# backend/app/schemas/copilot_schema.py
from datetime import datetime
from typing import Optional

from pydantic import Field

from app.schemas.common_schema import CamelModel


# ---------------------------------------------------------------------------
# Requests
# ---------------------------------------------------------------------------

class ConversationCreateRequest(CamelModel):
    title: Optional[str] = None


class ConversationRenameRequest(CamelModel):
    title: str


class ChatRequest(CamelModel):
    conversation_id: Optional[str] = None
    message: str


class ContextSearchRequest(CamelModel):
    query: str
    limit: int = 5


class FeedbackRequest(CamelModel):
    rating: str  # up | down
    comment: Optional[str] = None


# ---------------------------------------------------------------------------
# Responses
# ---------------------------------------------------------------------------

class CopilotToolCallResponse(CamelModel):
    name: str
    label: Optional[str] = None
    input: Optional[dict] = None


class CopilotSourceResponse(CamelModel):
    email_id: str
    snippet: str
    score: float


class CopilotMessageResponse(CamelModel):
    id: str
    role: str  # user | assistant
    content: str
    tool_calls: list[CopilotToolCallResponse] = Field(default_factory=list)
    sources: list[CopilotSourceResponse] = Field(default_factory=list)
    feedback: Optional[str] = None


class ConversationSummaryResponse(CamelModel):
    id: str
    title: str
    last_message_at: datetime


class ConversationListResponse(CamelModel):
    items: list[ConversationSummaryResponse]
    total: int


class ConversationDetailResponse(CamelModel):
    id: str
    title: str
    messages: list[CopilotMessageResponse] = Field(default_factory=list)


class ChatResponse(CamelModel):
    conversation_id: str
    message: CopilotMessageResponse


class ContextSearchResponse(CamelModel):
    results: list[CopilotSourceResponse]