# backend/app/services/inbox_service.py
"""
Inbox synchronization service.

Responsibilities:
  - trigger_inbox_sync: pulls new Gmail messages via the Gmail API,
    deduplicates against existing email documents, saves them to
    MongoDB, and enqueues each new message through the LangGraph
    multi-agent pipeline (ai/graph/email_pipeline.py).
  - get_sync_status: returns the last-sync timestamp and current
    sync state for the frontend's polling UI ("Syncing..." indicator).

Heavy lifting for Gmail message fetching is delegated to
  integrations/gmail/gmail_sync.py
AI pipeline processing is delegated to
  ai/graph/email_pipeline.py
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Optional

from app.exceptions.custom_exceptions import AppException
from app.integrations.gmail.gmail_sync import fetch_new_messages
from app.models.email import EmailModel
from app.repositories.email_repository import EmailRepository
from app.repositories.user_repository import UserRepository
from app.schemas.email_schema import SyncResultResponse, SyncStatusResponse

logger = logging.getLogger("ai_email_os.inbox_service")

# Simple in-memory sync-state tracker.
# In production with multiple workers, move this to Redis or a DB field.
_sync_state: dict[str, dict] = {}


def _get_state(user_id: str) -> dict:
    return _sync_state.setdefault(user_id, {"status": "idle", "last_synced_at": None})


async def trigger_inbox_sync(user_id: str, full_sync: bool = False) -> SyncResultResponse:
    """
    Initiates a Gmail inbox sync for the given user.

    Steps:
      1. Load user's Google OAuth tokens from the DB.
      2. Call integrations/gmail/gmail_sync.py:fetch_new_messages().
      3. Deduplicate by gmail_message_id — skip already-persisted emails.
      4. Persist new EmailModel documents to MongoDB.
      5. For each new email, kick off the LangGraph AI processing pipeline.
      6. Update the user's last_gmail_synced_at timestamp.

    Returns a SyncResultResponse with the count of newly synced emails.
    """
    state = _get_state(user_id)
    if state["status"] == "syncing":
        # Idempotent — don't allow concurrent syncs for the same user
        last = state.get("last_synced_at") or datetime.now(timezone.utc)
        return SyncResultResponse(synced_count=0, last_synced_at=last)

    state["status"] = "syncing"
    logger.info("Inbox sync started: user_id=%s full=%s", user_id, full_sync)

    try:
        user_repo = UserRepository()
        user = await user_repo.get_by_id(user_id)
        if not user or not user.oauth_tokens:
            raise AppException(status_code=400, detail="Gmail not connected. Please authenticate.")

        email_repo = EmailRepository()

        # Fetch raw Gmail message payloads (already parsed to dicts by gmail_sync)
        raw_messages = await fetch_new_messages(
            oauth_tokens=user.oauth_tokens,
            full_sync=full_sync,
        )

        synced_count = 0
        new_emails: list[EmailModel] = []

        for msg_data in raw_messages:
            gmail_msg_id: str = msg_data["gmail_message_id"]
            exists = await email_repo.find_one(
                {"user_id": user_id, "gmail_message_id": gmail_msg_id}
            )
            if exists:
                continue  # Already stored — skip

            email = EmailModel(
                user_id=user.id,
                gmail_thread_id=msg_data["gmail_thread_id"],
                gmail_message_id=gmail_msg_id,
                subject=msg_data.get("subject", ""),
                sender_name=msg_data.get("sender_name"),
                sender_email=msg_data.get("sender_email", ""),
                snippet=msg_data.get("snippet", ""),
                thread=msg_data.get("thread", []),
                received_at=msg_data.get("received_at", datetime.now(timezone.utc)),
                has_attachment=bool(msg_data.get("attachments")),
            )
            new_emails.append(email)

        if new_emails:
            # Bulk insert for speed, then process through AI pipeline
            for email in new_emails:
                saved = await email_repo.insert_one(email)
                synced_count += 1
                # Kick off async AI processing (fire-and-forget within the same event loop)
                try:
                    from app.ai.graph.email_pipeline import run_email_pipeline  # noqa: PLC0415
                    import asyncio  # noqa: PLC0415
                    asyncio.create_task(run_email_pipeline(email_id=str(saved.id), user_id=user_id))
                except Exception as ai_exc:
                    logger.warning(
                        "AI pipeline kick-off failed for email %s: %s", saved.id, ai_exc
                    )

        # Update last synced timestamp on user
        now = datetime.now(timezone.utc)
        await user_repo.update_one(
            {"_id": user.id},
            {"$set": {"oauth_tokens.last_gmail_synced_at": now, "updated_at": now}},
        )

        state["status"] = "idle"
        state["last_synced_at"] = now
        logger.info("Inbox sync complete: user_id=%s synced=%d", user_id, synced_count)
        return SyncResultResponse(synced_count=synced_count, last_synced_at=now)

    except AppException:
        state["status"] = "error"
        raise
    except Exception as exc:
        state["status"] = "error"
        logger.exception("Inbox sync error for user_id=%s: %s", user_id, exc)
        raise AppException(status_code=500, detail="Inbox sync failed.") from exc


async def get_sync_status(user_id: str) -> SyncStatusResponse:
    """
    Returns the current sync state for the user.
    Used by the frontend's polling indicator (InboxPage "Syncing..." badge).
    """
    state = _get_state(user_id)

    # Also check DB for last_gmail_synced_at if in-memory state is cold (e.g. after restart)
    last_synced_at: Optional[datetime] = state.get("last_synced_at")
    if last_synced_at is None:
        user_repo = UserRepository()
        user = await user_repo.get_by_id(user_id)
        if user and user.oauth_tokens and user.oauth_tokens.last_gmail_synced_at:
            last_synced_at = user.oauth_tokens.last_gmail_synced_at
            state["last_synced_at"] = last_synced_at

    return SyncStatusResponse(
        status=state.get("status", "idle"),
        last_synced_at=last_synced_at,
    )

