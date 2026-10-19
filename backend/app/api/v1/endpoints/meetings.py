# backend/app/api/v1/endpoints/meetings.py
"""
Meeting CRUD + Google Calendar sync. Maps 1:1 to
frontend/src/api/meetingApi.js.
"""

from typing import Optional

from fastapi import APIRouter, Depends, Query

from app.schemas.meeting_schema import (
    MeetingListResponse,
    MeetingResponse,
    MeetingCreateRequest,
    MeetingUpdateRequest,
    MeetingStatsResponse,
)
from app.services.meeting_service import (
    list_meetings,
    get_meeting_by_id,
    create_meeting,
    update_meeting,
    update_meeting_status,
    delete_meeting,
    get_upcoming_meetings,
    get_meeting_stats,
)
from app.integrations.calendar.calendar_client import (
    sync_meeting_to_calendar,
    unsync_meeting_from_calendar,
)
from app.auth.jwt_handler import get_current_user

router = APIRouter()


@router.get("", response_model=MeetingListResponse)
async def get_meetings(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100, alias="pageSize"),
    status: Optional[str] = None,
    source: Optional[str] = None,
    email_id: Optional[str] = Query(None, alias="emailId"),
    from_date: Optional[str] = Query(None, alias="fromDate"),
    to_date: Optional[str] = Query(None, alias="toDate"),
    sort_by: str = Query("start_time", alias="sortBy"),
    sort_order: str = Query("asc", alias="sortOrder"),
    current_user=Depends(get_current_user),
):
    return await list_meetings(
        user_id=current_user.id,
        page=page,
        page_size=page_size,
        status=status,
        source=source,
        email_id=email_id,
        from_date=from_date,
        to_date=to_date,
        sort_by=sort_by,
        sort_order=sort_order,
    )


@router.get("/upcoming")
async def upcoming_meetings(days: int = 7, current_user=Depends(get_current_user)):
    return await get_upcoming_meetings(user_id=current_user.id, days=days)


@router.get("/stats", response_model=MeetingStatsResponse)
async def meeting_stats(current_user=Depends(get_current_user)):
    return await get_meeting_stats(user_id=current_user.id)


@router.get("/{meeting_id}", response_model=MeetingResponse)
async def get_meeting(meeting_id: str, current_user=Depends(get_current_user)):
    return await get_meeting_by_id(user_id=current_user.id, meeting_id=meeting_id)


@router.post("", response_model=MeetingResponse, status_code=201)
async def create_meeting_route(payload: MeetingCreateRequest, current_user=Depends(get_current_user)):
    return await create_meeting(user_id=current_user.id, payload=payload)


@router.patch("/{meeting_id}", response_model=MeetingResponse)
async def update_meeting_route(meeting_id: str, payload: MeetingUpdateRequest, current_user=Depends(get_current_user)):
    return await update_meeting(user_id=current_user.id, meeting_id=meeting_id, payload=payload)


@router.patch("/{meeting_id}/status", response_model=MeetingResponse)
async def update_status(meeting_id: str, status: str, current_user=Depends(get_current_user)):
    """Used by confirmMeeting()/declineMeeting() on the frontend, passing status in the body via a small payload."""
    return await update_meeting_status(user_id=current_user.id, meeting_id=meeting_id, status=status)


@router.post("/{meeting_id}/sync-calendar", response_model=MeetingResponse)
async def sync_to_calendar(meeting_id: str, current_user=Depends(get_current_user)):
    """Pushes a confirmed meeting to Google Calendar via the Calendar API integration."""
    return await sync_meeting_to_calendar(user_id=current_user.id, meeting_id=meeting_id)


@router.delete("/{meeting_id}/sync-calendar", response_model=MeetingResponse)
async def unsync_from_calendar(meeting_id: str, current_user=Depends(get_current_user)):
    """Removes the meeting from Google Calendar, keeps the local record."""
    return await unsync_meeting_from_calendar(user_id=current_user.id, meeting_id=meeting_id)


@router.delete("/{meeting_id}", status_code=204)
async def delete_meeting_route(meeting_id: str, current_user=Depends(get_current_user)):
    await delete_meeting(user_id=current_user.id, meeting_id=meeting_id)