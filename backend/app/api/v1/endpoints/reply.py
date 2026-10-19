# backend/app/api/v1/endpoints/reply.py
"""
AI reply generation + sending. Sub-resource of /emails/{email_id} —
maps to emailApi.js's generateReply()/sendReply().
"""

from fastapi import APIRouter, Depends

from app.schemas.email_schema import (
    GenerateReplyRequest,
    GenerateReplyResponse,
    SendReplyRequest,
    SendReplyResponse,
)
from app.services.reply_service import generate_reply_drafts, send_reply
from app.auth.jwt_handler import get_current_user

router = APIRouter()


@router.post("/{email_id}/reply/generate", response_model=GenerateReplyResponse)
async def generate_reply(email_id: str, payload: GenerateReplyRequest, current_user=Depends(get_current_user)):
    """
    Invokes the Reply Agent (Gemini + email context + RAG) to produce
    one or more tone-variant reply drafts for the given email.
    """
    drafts = await generate_reply_drafts(
        user_id=current_user.id,
        email_id=email_id,
        tone=payload.tone,
        instructions=payload.instructions,
    )
    return GenerateReplyResponse(drafts=drafts)


@router.post("/{email_id}/reply/send", response_model=SendReplyResponse)
async def send_reply_route(email_id: str, payload: SendReplyRequest, current_user=Depends(get_current_user)):
    """Sends a reply (AI draft, edited draft, or fully manual) via the Gmail API."""
    result = await send_reply(
        user_id=current_user.id,
        email_id=email_id,
        body=payload.body,
        draft_id=payload.draft_id,
    )
    return result