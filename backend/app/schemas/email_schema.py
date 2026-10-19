# backend/app/schemas/email_schema.py
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.schemas.common_schema import CamelModel


# ---------------------------------------------------------------------------
# Requests
# ---------------------------------------------------------------------------

class SyncInboxRequest(CamelModel):
    full: bool = False


class EmailReadUpdateRequest(CamelModel):
    is_read: bool = True


class EmailArchiveUpdateRequest(CamelModel):
    archived: bool = True


class BulkActionRequest(CamelModel):
    email_ids: list[str]
    action: str  # archive | delete | mark_read | mark_unread


class SemanticSearchRequest(CamelModel):
    query: str
    limit: int = 10


class GenerateReplyRequest(CamelModel):
    tone: Optional[str] = "friendly"  # formal | friendly | concise
    instructions: Optional[str] = None


class SendReplyRequest(CamelModel):
    body: str
    draft_id: Optional[str] = None


# ---------------------------------------------------------------------------
# Responses
# ---------------------------------------------------------------------------

class SyncResultResponse(CamelModel):
    synced_count: int
    last_synced_at: datetime


class SyncStatusResponse(CamelModel):
    status: str  # idle | syncing | error
    last_synced_at: Optional[datetime] = None


class EmailAttachmentResponse(CamelModel):
    id: str
    filename: str
    download_url: str
    size_bytes: Optional[int] = None


class EmailListItemResponse(CamelModel):
    id: str
    sender_name: Optional[str] = None
    sender_email: str
    subject: str
    snippet: str
    ai_summary: Optional[str] = None
    is_read: bool
    is_starred: bool
    has_attachment: bool
    has_meeting: bool
    has_task: bool
    pending_reply: bool = False
    priority: Optional[str] = None
    category: Optional[str] = None
    intent: Optional[str] = None
    sentiment: Optional[str] = None
    received_at_label: str
    received_at: datetime


class EmailListResponse(CamelModel):
    items: list[EmailListItemResponse]
    total: int
    page: int
    page_size: int


class ThreadMessageResponse(CamelModel):
    id: str
    sender_name: Optional[str] = None
    sender_email: str
    recipients_label: Optional[str] = None
    snippet: str
    body_html: Optional[str] = None
    body_text: Optional[str] = None
    sent_at_label: str
    sent_at: datetime
    attachments: list[EmailAttachmentResponse] = Field(default_factory=list)


class DetectedMeetingRefResponse(CamelModel):
    id: str
    title: str
    start_time_label: str
    location: Optional[str] = None
    status: str


class DetectedTaskRefResponse(CamelModel):
    id: str
    title: str
    due_date_label: Optional[str] = None
    status: str


class EmailDetailResponse(EmailListItemResponse):
    thread: list[ThreadMessageResponse] = Field(default_factory=list)
    ai_key_points: list[str] = Field(default_factory=list)
    detected_meetings: list[DetectedMeetingRefResponse] = Field(default_factory=list)
    detected_tasks: list[DetectedTaskRefResponse] = Field(default_factory=list)


class EmailSummaryResponse(CamelModel):
    summary: str


class ReplyDraftResponse(CamelModel):
    id: str
    tone: str
    body: str


class GenerateReplyResponse(CamelModel):
    drafts: list[ReplyDraftResponse]


class SendReplyResponse(CamelModel):
    id: str
    sent: bool = True
    sent_at: datetime


class SemanticSearchResultResponse(CamelModel):
    email_id: str
    snippet: str
    score: float


class SemanticSearchResponse(CamelModel):
    results: list[SemanticSearchResultResponse]