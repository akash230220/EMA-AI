# backend/app/models/email.py
"""
Email document — one per synced Gmail message/thread. This is the
central model the entire AI pipeline (LangGraph agents) writes its
output onto: category, priority, intent, sentiment, ai_summary,
ai_key_points, detected meeting/task references.
"""

from datetime import datetime
from typing import Optional

from pydantic import Field

from app.models.base import MongoBaseModel, PyObjectId, utcnow


class EmailAttachment(MongoBaseModel.__base__):
    model_config = {"populate_by_name": True}

    id: str
    filename: str
    mime_type: Optional[str] = None
    size_bytes: Optional[int] = None
    gmail_attachment_id: str  # used to lazily fetch/download via Gmail API


class ThreadMessage(MongoBaseModel.__base__):
    """One physical message within a Gmail thread — embedded, not a separate collection."""

    model_config = {"populate_by_name": True}

    id: str  # Gmail message id
    sender_name: Optional[str] = None
    sender_email: str
    recipients: list[str] = Field(default_factory=list)
    snippet: str = ""
    body_html: Optional[str] = None
    body_text: Optional[str] = None
    sent_at: datetime
    attachments: list[EmailAttachment] = Field(default_factory=list)


class DetectedMeetingRef(MongoBaseModel.__base__):
    """Denormalized pointer to a Meeting doc detected from this email — avoids a join for EmailDetailPage."""

    model_config = {"populate_by_name": True}

    meeting_id: PyObjectId
    title: str
    start_time: datetime
    status: str  # detected | confirmed | declined | synced


class DetectedTaskRef(MongoBaseModel.__base__):
    model_config = {"populate_by_name": True}

    task_id: PyObjectId
    title: str
    status: str  # pending | in_progress | completed | dismissed


class EmailModel(MongoBaseModel):
    """Collection: `emails`"""

    user_id: PyObjectId
    gmail_thread_id: str = Field(..., description="Gmail's thread id — groups ThreadMessages.")
    gmail_message_id: str = Field(..., description="The latest/primary message id in the thread.")

    subject: str = ""
    sender_name: Optional[str] = None
    sender_email: str
    snippet: str = ""
    thread: list[ThreadMessage] = Field(default_factory=list)

    # --- AI-derived fields (written by the LangGraph pipeline) ---
    category: Optional[str] = None  # work | finance | personal | newsletters | promotions | social
    priority: Optional[str] = None  # high | medium | low
    intent: Optional[str] = None  # meeting_request | task | fyi | follow_up | urgent_action | question
    sentiment: Optional[str] = None  # positive | neutral | negative
    ai_summary: Optional[str] = None
    ai_key_points: list[str] = Field(default_factory=list)
    ai_processed_at: Optional[datetime] = None
    ai_pipeline_version: Optional[str] = None  # for cache-busting reprocessing after prompt changes

    detected_meetings: list[DetectedMeetingRef] = Field(default_factory=list)
    detected_tasks: list[DetectedTaskRef] = Field(default_factory=list)

    # --- User/state flags ---
    is_read: bool = False
    is_starred: bool = False
    archived: bool = False
    deleted: bool = False  # soft delete
    pending_reply: bool = False
    has_attachment: bool = False

    received_at: datetime
    replied_at: Optional[datetime] = None

    # --- RAG bookkeeping ---
    embedding_indexed: bool = False
    embedding_indexed_at: Optional[datetime] = None

    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)


class ReplyDraftModel(MongoBaseModel):
    """
    Collection: `reply_drafts` — AI-generated reply options for a
    given email, kept as their own collection (rather than embedded
    on EmailModel) since drafts are ephemeral/regenerable and can be
    numerous across tone variants + regenerations.
    """

    user_id: PyObjectId
    email_id: PyObjectId
    tone: str  # formal | friendly | concise
    body: str
    instructions: Optional[str] = None
    created_at: datetime = Field(default_factory=utcnow)