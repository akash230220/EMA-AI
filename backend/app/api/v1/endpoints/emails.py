# backend/app/api/v1/endpoints/emails.py
"""
Email CRUD, filtering, AI reprocessing, and semantic search.
Maps to the non-reply methods of frontend/src/api/emailApi.js.
"""

from typing import Optional

from fastapi import APIRouter, Depends, Query

from app.schemas.common_schema import BulkActionResponse
from app.schemas.email_schema import (
    EmailListResponse,
    EmailDetailResponse,
    EmailReadUpdateRequest,
    EmailArchiveUpdateRequest,
    BulkActionRequest,
    SemanticSearchRequest,
    SemanticSearchResponse,
    EmailSummaryResponse,
)
from app.services.email_service import (
    list_emails,
    get_email_by_id,
    set_email_read_status,
    set_email_archived_status,
    delete_email,
    reprocess_email,
    get_email_summary,
    bulk_action_emails,
)
from app.ai.rag.vectorstore.chroma_client import semantic_search_emails
from app.auth.jwt_handler import get_current_user

router = APIRouter()


@router.get("", response_model=EmailListResponse)
async def get_emails(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100, alias="pageSize"),
    category: Optional[str] = None,
    priority: Optional[str] = None,
    intent: Optional[str] = None,
    sentiment: Optional[str] = None,
    unread_only: Optional[bool] = Query(None, alias="unreadOnly"),
    pending_reply_only: Optional[bool] = Query(None, alias="pendingReplyOnly"),
    archived: Optional[bool] = None,
    search: Optional[str] = None,
    sort_by: str = Query("date", alias="sortBy"),
    sort_order: str = Query("desc", alias="sortOrder"),
    current_user=Depends(get_current_user),
):
    """Paginated, filterable email list — mirrors emailApi.getEmails(params)."""
    return await list_emails(
        user_id=current_user.id,
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


@router.get("/search/semantic", response_model=SemanticSearchResponse)
async def search_semantic_get(q: str = Query(..., min_length=1), limit: int = 10, current_user=Depends(get_current_user)):
    """GET variant for quick semantic search (POST version below matches emailApi.semanticSearch exactly)."""
    results = await semantic_search_emails(user_id=current_user.id, query=q, limit=limit)
    return SemanticSearchResponse(results=results)


@router.post("/search/semantic", response_model=SemanticSearchResponse)
async def search_semantic(payload: SemanticSearchRequest, current_user=Depends(get_current_user)):
    """RAG semantic search over historical emails via ChromaDB — matches emailApi.semanticSearch()."""
    results = await semantic_search_emails(user_id=current_user.id, query=payload.query, limit=payload.limit)
    return SemanticSearchResponse(results=results)


@router.post("/bulk", response_model=BulkActionResponse)
async def bulk_action(payload: BulkActionRequest, current_user=Depends(get_current_user)):
    """Applies archive/delete/mark_read/mark_unread to multiple emails — matches emailApi.bulkAction()."""
    affected = await bulk_action_emails(user_id=current_user.id, email_ids=payload.email_ids, action=payload.action)
    return BulkActionResponse(affected=affected)


@router.get("/{email_id}", response_model=EmailDetailResponse)
async def get_email(email_id: str, current_user=Depends(get_current_user)):
    """Full thread + AI-derived fields for a single email."""
    return await get_email_by_id(user_id=current_user.id, email_id=email_id)


@router.patch("/{email_id}/read", response_model=EmailDetailResponse)
async def mark_read(email_id: str, payload: EmailReadUpdateRequest, current_user=Depends(get_current_user)):
    return await set_email_read_status(user_id=current_user.id, email_id=email_id, is_read=payload.is_read)


@router.patch("/{email_id}/archive", response_model=EmailDetailResponse)
async def set_archived(email_id: str, payload: EmailArchiveUpdateRequest, current_user=Depends(get_current_user)):
    return await set_email_archived_status(user_id=current_user.id, email_id=email_id, archived=payload.archived)


@router.delete("/{email_id}", status_code=204)
async def delete_email_route(email_id: str, current_user=Depends(get_current_user)):
    await delete_email(user_id=current_user.id, email_id=email_id)


@router.post("/{email_id}/reprocess", response_model=EmailDetailResponse)
async def reprocess(email_id: str, current_user=Depends(get_current_user)):
    """
    Re-runs the full LangGraph agent pipeline (categorization, intent,
    priority, sentiment, summarization, task/meeting extraction) on a
    single email.
    """
    return await reprocess_email(user_id=current_user.id, email_id=email_id)


@router.get("/{email_id}/summary", response_model=EmailSummaryResponse)
async def get_summary(email_id: str, current_user=Depends(get_current_user)):
    summary = await get_email_summary(user_id=current_user.id, email_id=email_id)
    return EmailSummaryResponse(summary=summary)