# backend/app/services/email_service.py
"""
Email CRUD and AI operations service.

Responsibilities:
  - list_emails       — paginated, filtered email list (InboxPage)
  - get_email_by_id   — full thread + AI fields (EmailDetailPage)
  - set_email_read_status  — mark read/unread
  - set_email_archived_status — archive/unarchive
  - delete_email      — soft-delete
  - reprocess_email   — re-runs the full LangGraph AI pipeline
  - get_email_summary — returns/generates the AI summary on demand
  - bulk_action_emails — bulk archive/delete/mark read operations

All Mongo I/O goes through EmailRepository.
AI reprocessing delegates to ai/graph/email_pipeline.py.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Optional

from app.exceptions.custom_exceptions import AppException
from app.repositories.email_repository import EmailRepository
from app.schemas.email_schema import (
    EmailDetailResponse,
    EmailListItemResponse,
    EmailListResponse,
    EmailSummaryResponse,
    ThreadMessageResponse,
    EmailAttachmentResponse,
    DetectedMeetingRefResponse,
    DetectedTaskRefResponse,
)
from app.models.email import EmailModel
from app.utils.datetime_utils import format_datetime_label

logger = logging.getLogger("ai_email_os.email_service")


# ---------------------------------------------------------------------------
# Private mapping helpers — EmailModel -> response schemas
# ---------------------------------------------------------------------------

def _format_received_at(dt: datetime) -> str:
    return format_datetime_label(dt)


def _to_list_item(email: EmailModel) -> EmailListItemResponse:
    return EmailListItemResponse(
        id=str(email.id),
        sender_name=email.sender_name,
        sender_email=email.sender_email,
        subject=email.subject,
        snippet=email.snippet,
        ai_summary=email.ai_summary,
        is_read=email.is_read,
        is_starred=email.is_starred,
        has_attachment=email.has_attachment,
        has_meeting=bool(email.detected_meetings),
        has_task=bool(email.detected_tasks),
        pending_reply=email.pending_reply,
        priority=email.priority,
        category=email.category,
        intent=email.intent,
        sentiment=email.sentiment,
        received_at_label=_format_received_at(email.received_at),
        received_at=email.received_at,
    )


def _to_detail(email: EmailModel) -> EmailDetailResponse:
    thread_responses = []
    for msg in email.thread:
        attachments = [
            EmailAttachmentResponse(
                id=att.id,
                filename=att.filename,
                download_url=f"/api/v1/emails/{email.id}/attachments/{att.gmail_attachment_id}",
                size_bytes=att.size_bytes,
            )
            for att in msg.attachments
        ]
        thread_responses.append(
            ThreadMessageResponse(
                id=msg.id,
                sender_name=msg.sender_name,
                sender_email=msg.sender_email,
                recipients_label=", ".join(msg.recipients) if msg.recipients else None,
                snippet=msg.snippet,
                body_html=msg.body_html,
                body_text=msg.body_text,
                sent_at_label=format_datetime_label(msg.sent_at),
                sent_at=msg.sent_at,
                attachments=attachments,
            )
        )

    meetings = [
        DetectedMeetingRefResponse(
            id=str(m.meeting_id),
            title=m.title,
            start_time_label=format_datetime_label(m.start_time),
            status=m.status,
        )
        for m in email.detected_meetings
    ]

    tasks = [
        DetectedTaskRefResponse(
            id=str(t.task_id),
            title=t.title,
            status=t.status,
        )
        for t in email.detected_tasks
    ]

    base = _to_list_item(email)
    return EmailDetailResponse(
        **base.model_dump(),
        thread=thread_responses,
        ai_key_points=email.ai_key_points,
        detected_meetings=meetings,
        detected_tasks=tasks,
    )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

async def list_emails(
    user_id: str,
    *,
    page: int = 1,
    page_size: int = 20,
    category: Optional[str] = None,
    priority: Optional[str] = None,
    intent: Optional[str] = None,
    sentiment: Optional[str] = None,
    unread_only: Optional[bool] = None,
    pending_reply_only: Optional[bool] = None,
    archived: Optional[bool] = None,
    search: Optional[str] = None,
    sort_by: str = "received_at",
    sort_order: str = "desc",
) -> EmailListResponse:
    """
    Returns a paginated, filtered list of emails for InboxPage.
    Delegates all filtering/sorting/pagination to EmailRepository.
    """
    repo = EmailRepository()
    emails, total = await repo.list_for_user(
        user_id=user_id,
        page=page,
        page_size=page_size,
        category=category,
        priority=priority,
        intent=intent,
        sentiment=sentiment,
        unread_only=unread_only,
        pending_reply_only=pending_reply_only,
        archived=archived,
        search=search,
        sort_by=sort_by,
        sort_order=sort_order,
    )
    return EmailListResponse(
        items=[_to_list_item(e) for e in emails],
        total=total,
        page=page,
        page_size=page_size,
    )


async def get_email_by_id(user_id: str, email_id: str) -> EmailDetailResponse:
    """
    Returns the full email detail including thread messages, AI fields,
    and detected meetings/tasks. Used by EmailDetailPage.
    """
    repo = EmailRepository()
    email = await repo.get_for_user(user_id=user_id, email_id=email_id)
    if not email:
        raise AppException(status_code=404, detail="Email not found.")

    # Auto-mark as read on open (mirrors Gmail behaviour; can be made
    # optional via an AI preference setting in the future)
    if not email.is_read:
        email = await repo.mark_read(user_id=user_id, email_id=email_id, is_read=True)

    return _to_detail(email)


async def set_email_read_status(
    user_id: str, email_id: str, is_read: bool
) -> EmailDetailResponse:
    """Marks an email read or unread."""
    repo = EmailRepository()
    email = await repo.mark_read(user_id=user_id, email_id=email_id, is_read=is_read)
    if not email:
        raise AppException(status_code=404, detail="Email not found.")
    return _to_detail(email)


async def set_email_archived_status(
    user_id: str, email_id: str, archived: bool
) -> EmailDetailResponse:
    """Archives or unarchives an email."""
    repo = EmailRepository()
    email = await repo.mark_archived(user_id=user_id, email_id=email_id, archived=archived)
    if not email:
        raise AppException(status_code=404, detail="Email not found.")
    return _to_detail(email)


async def delete_email(user_id: str, email_id: str) -> None:
    """Soft-deletes an email (sets deleted=True, does not remove from DB)."""
    repo = EmailRepository()
    deleted = await repo.soft_delete(user_id=user_id, email_id=email_id)
    if not deleted:
        raise AppException(status_code=404, detail="Email not found.")


async def reprocess_email(user_id: str, email_id: str) -> EmailDetailResponse:
    """
    Re-runs the full LangGraph multi-agent AI pipeline on a single
    email. Useful after AI model updates (ai_pipeline_version bump) or
    when the user manually triggers reprocessing from the EmailDetailPage.
    """
    repo = EmailRepository()
    email = await repo.get_for_user(user_id=user_id, email_id=email_id)
    if not email:
        raise AppException(status_code=404, detail="Email not found.")

    try:
        from app.ai.graph.email_pipeline import run_email_pipeline  # noqa: PLC0415
        await run_email_pipeline(email_id=email_id, user_id=user_id)
    except Exception as exc:
        logger.exception("Reprocess pipeline failed for email %s: %s", email_id, exc)
        raise AppException(status_code=500, detail="AI reprocessing failed.") from exc

    # Reload from DB after pipeline has written its results
    email = await repo.get_for_user(user_id=user_id, email_id=email_id)
    if not email:
        raise AppException(status_code=404, detail="Email not found after reprocessing.")
    return _to_detail(email)


async def get_email_summary(user_id: str, email_id: str) -> str:
    """
    Returns the cached AI summary for an email, or generates one
    on-demand via Gemini if it hasn't been set yet.
    """
    repo = EmailRepository()
    email = await repo.get_for_user(user_id=user_id, email_id=email_id)
    if not email:
        raise AppException(status_code=404, detail="Email not found.")

    if email.ai_summary:
        return email.ai_summary

    # Generate on-demand via the summarization agent
    try:
        from app.ai.agents.summarization_agent import generate_summary_for_email  # noqa: PLC0415
        summary = await generate_summary_for_email(email=email)
    except Exception as exc:
        logger.exception("On-demand summary generation failed for email %s: %s", email_id, exc)
        raise AppException(status_code=500, detail="Summary generation failed.") from exc

    # Persist the generated summary
    await repo.update_one(
        {"_id": email.id, "user_id": user_id},
        {"$set": {"ai_summary": summary, "updated_at": datetime.now(timezone.utc)}},
    )
    return summary


async def bulk_action_emails(
    user_id: str, email_ids: list[str], action: str
) -> int:
    """
    Applies a bulk action (archive | delete | mark_read | mark_unread)
    to a list of email ids. Returns the count of affected documents.
    """
    valid_actions = {"archive", "unarchive", "delete", "mark_read", "mark_unread"}
    if action not in valid_actions:
        raise AppException(
            status_code=422,
            detail=f"Invalid action '{action}'. Must be one of: {', '.join(valid_actions)}.",
        )

    repo = EmailRepository()
    affected = await repo.bulk_update(user_id=user_id, email_ids=email_ids, action=action)
    logger.info(
        "Bulk action '%s' applied to %d emails for user_id=%s", action, affected, user_id
    )
    return affected

