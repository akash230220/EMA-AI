# backend/app/services/reply_service.py
"""
AI Reply generation and Gmail send service.

Responsibilities:
  - generate_reply_drafts: invokes the Reply Agent (Gemini + email
    context + optional RAG retrieval from ChromaDB) to produce one or
    more tone-variant draft bodies, persisted as ReplyDraftModel docs.
  - send_reply: sends a reply body via the Gmail API, marks the
    source email as replied, and increments analytics counters.

AI generation delegates to ai/agents/reply_agent.py.
Gmail send delegates to integrations/gmail/gmail_client.py.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Optional

from app.exceptions.custom_exceptions import AppException
from app.models.email import ReplyDraftModel
from app.repositories.email_repository import EmailRepository
from app.repositories.user_repository import UserRepository
from app.schemas.email_schema import ReplyDraftResponse, SendReplyResponse

logger = logging.getLogger("ai_email_os.reply_service")

# Collection name for reply drafts — accessed directly (no typed repo needed)
REPLY_DRAFTS_COLLECTION = "reply_drafts"


async def _get_reply_drafts_collection():
    from app.db.mongo_client import get_database  # noqa: PLC0415
    return get_database()[REPLY_DRAFTS_COLLECTION]


async def generate_reply_drafts(
    user_id: str,
    email_id: str,
    tone: Optional[str] = "friendly",
    instructions: Optional[str] = None,
) -> list[ReplyDraftResponse]:
    """
    Generates AI reply drafts for the given email.

    For each requested tone (or just the specified tone), the Reply
    Agent is invoked with:
      - the full email thread text
      - the user's AI preferences (default_reply_tone)
      - optional custom instructions from the ReplyComposer
      - RAG context: semantically similar past replies fetched from ChromaDB

    Each draft body is persisted as a ReplyDraftModel document so the
    user can come back to it, edit it, and send it without regenerating.

    Returns a list of ReplyDraftResponse objects.
    """
    email_repo = EmailRepository()
    email = await email_repo.get_for_user(user_id=user_id, email_id=email_id)
    if not email:
        raise AppException(status_code=404, detail="Email not found.")

    user_repo = UserRepository()
    user = await user_repo.get_by_id(user_id)
    if not user:
        raise AppException(status_code=404, detail="User not found.")

    # Determine tones to generate:
    # - If tone is "all", generate formal / friendly / concise variants
    # - Otherwise generate only the requested tone
    tones_to_generate: list[str]
    if tone == "all":
        tones_to_generate = ["formal", "friendly", "concise"]
    else:
        tones_to_generate = [tone or user.ai_preferences.default_reply_tone]

    # Build the email thread text for the agent
    thread_text = "\n\n".join(
        f"From: {msg.sender_email}\n{msg.body_text or msg.snippet}"
        for msg in email.thread
    ) or email.snippet

    drafts: list[ReplyDraftResponse] = []
    col = await _get_reply_drafts_collection()

    for t in tones_to_generate:
        try:
            from app.ai.agents.reply_agent import generate_reply  # noqa: PLC0415
            body = await generate_reply(
                thread_text=thread_text,
                tone=t,
                instructions=instructions,
                user_id=user_id,
            )
        except Exception as exc:
            logger.exception(
                "Reply Agent failed for email %s tone=%s: %s", email_id, t, exc
            )
            raise AppException(status_code=500, detail=f"Reply generation failed for tone '{t}'.") from exc

        draft = ReplyDraftModel(
            user_id=email.user_id,
            email_id=email.id,
            tone=t,
            body=body,
            instructions=instructions,
        )
        doc = draft.model_dump(by_alias=True)
        result = await col.insert_one(doc)
        doc["_id"] = result.inserted_id

        drafts.append(
            ReplyDraftResponse(
                id=str(result.inserted_id),
                tone=t,
                body=body,
            )
        )

    logger.info(
        "Generated %d reply draft(s) for email %s user_id=%s",
        len(drafts), email_id, user_id,
    )
    return drafts


async def send_reply(
    user_id: str,
    email_id: str,
    body: str,
    draft_id: Optional[str] = None,
) -> SendReplyResponse:
    """
    Sends a reply to the given email via the Gmail API.

    Steps:
      1. Fetch the source email (for thread_id, recipient address).
      2. Fetch the user's OAuth tokens.
      3. Call gmail_client.send_reply_message().
      4. Mark the source email as pending_reply=False, replied_at=now.
      5. If a draft_id was provided, clean up the draft doc.

    Returns a SendReplyResponse with confirmation.
    """
    email_repo = EmailRepository()
    email = await email_repo.get_for_user(user_id=user_id, email_id=email_id)
    if not email:
        raise AppException(status_code=404, detail="Email not found.")

    user_repo = UserRepository()
    user = await user_repo.get_by_id(user_id)
    if not user or not user.oauth_tokens:
        raise AppException(
            status_code=400,
            detail="Gmail not connected. Cannot send reply.",
        )

    try:
        from app.integrations.gmail.gmail_client import send_reply_message  # noqa: PLC0415
        sent_message_id = await send_reply_message(
            oauth_tokens=user.oauth_tokens,
            thread_id=email.gmail_thread_id,
            to_address=email.sender_email,
            subject=email.subject,
            body=body,
        )
    except Exception as exc:
        logger.exception("Gmail send failed for email %s: %s", email_id, exc)
        raise AppException(status_code=500, detail="Failed to send reply via Gmail.") from exc

    now = datetime.now(timezone.utc)

    # Mark source email as replied
    await email_repo.update_one(
        {"_id": email.id, "user_id": user_id},
        {"$set": {"pending_reply": False, "replied_at": now, "updated_at": now}},
    )

    # Delete the used draft if one was provided
    if draft_id:
        try:
            col = await _get_reply_drafts_collection()
            from bson import ObjectId  # noqa: PLC0415
            if ObjectId.is_valid(draft_id):
                await col.delete_one({"_id": ObjectId(draft_id), "user_id": user.id})
        except Exception:
            pass  # Non-critical — log but don't fail the send

    logger.info(
        "Reply sent: email_id=%s gmail_message_id=%s user_id=%s",
        email_id, sent_message_id, user_id,
    )
    return SendReplyResponse(
        id=sent_message_id,
        sent=True,
        sent_at=now,
    )

