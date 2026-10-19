# backend/app/api/v1/endpoints/inbox.py
"""
Inbox sync endpoints. Maps to emailApi.js's syncInbox()/getSyncStatus().
"""

from fastapi import APIRouter, Depends

from app.schemas.email_schema import SyncInboxRequest, SyncStatusResponse, SyncResultResponse
from app.services.inbox_service import trigger_inbox_sync, get_sync_status
from app.auth.jwt_handler import get_current_user

router = APIRouter()


@router.post("/sync", response_model=SyncResultResponse)
async def sync_inbox(payload: SyncInboxRequest, current_user=Depends(get_current_user)):
    """
    Triggers a Gmail inbox sync for the current user. Fetches new
    messages via the Gmail API and enqueues them through the
    LangGraph multi-agent pipeline (ai/graph/email_pipeline.py).
    """
    result = await trigger_inbox_sync(user_id=current_user.id, full_sync=payload.full)
    return result


@router.get("/sync/status", response_model=SyncStatusResponse)
async def sync_status(current_user=Depends(get_current_user)):
    """Returns the current sync status — used for a polling 'Syncing...' UI state."""
    return await get_sync_status(user_id=current_user.id)