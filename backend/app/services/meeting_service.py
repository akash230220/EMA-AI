# backend/app/services/meeting_service.py
"""
Meeting CRUD and statistics service.

Responsibilities:
  - list_meetings        — paginated, filtered meeting list (MeetingsPage)
  - get_meeting_by_id    — single meeting detail
  - create_meeting       — manual meeting creation
  - update_meeting       — field-level update
  - update_meeting_status — status transition (detected → confirmed | declined | synced)
  - delete_meeting       — remove meeting document
  - get_upcoming_meetings — next N days of confirmed/detected meetings (Dashboard widget)
  - get_meeting_stats    — summary counts for Dashboard StatCard

All Mongo I/O goes through MeetingRepository.
Google Calendar sync is handled by calendar_client.py (called by the endpoint).
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

from app.exceptions.custom_exceptions import AppException
from app.models.meeting import MeetingModel
from app.repositories.meeting_repository import MeetingRepository
from app.repositories.user_repository import UserRepository
from app.schemas.meeting_schema import (
    DateShortLabel,
    MeetingCreateRequest,
    MeetingListResponse,
    MeetingResponse,
    MeetingStatsResponse,
    MeetingUpdateRequest,
)
from app.utils.datetime_utils import format_datetime_label

logger = logging.getLogger("ai_email_os.meeting_service")

VALID_STATUSES = {"detected", "confirmed", "declined", "synced"}


# ---------------------------------------------------------------------------
# Mapping helper
# ---------------------------------------------------------------------------

def _to_response(meeting: MeetingModel) -> MeetingResponse:
    start_label = format_datetime_label(meeting.start_time)
    end_label = format_datetime_label(meeting.end_time)

    # Short date label for MeetingCard badge (e.g. "Aug / 26")
    date_short = DateShortLabel(
        month=meeting.start_time.strftime("%b"),
        day=meeting.start_time.strftime("%d").lstrip("0"),
    )

    # Group label for MeetingList date dividers (e.g. "Today", "Tomorrow", "Aug 27")
    today = datetime.now(timezone.utc).date()
    meeting_date = meeting.start_time.date()
    if meeting_date == today:
        group_label = "Today"
    elif meeting_date == today + timedelta(days=1):
        group_label = "Tomorrow"
    else:
        group_label = meeting.start_time.strftime("%-d %b %Y")

    return MeetingResponse(
        id=str(meeting.id),
        title=meeting.title,
        start_time=meeting.start_time,
        end_time=meeting.end_time,
        start_time_label=start_label,
        end_time_label=end_label,
        date_short_label=date_short,
        date_group_label=group_label,
        location=meeting.location,
        description=meeting.description,
        attendees=meeting.attendees,
        status=meeting.status,
        source=meeting.source,
        source_email_id=str(meeting.source_email_id) if meeting.source_email_id else None,
        calendar_event_id=meeting.calendar_event_id,
    )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

async def list_meetings(
    user_id: str,
    *,
    page: int = 1,
    page_size: int = 20,
    status: Optional[str] = None,
    source: Optional[str] = None,
    email_id: Optional[str] = None,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    sort_by: str = "start_time",
    sort_order: str = "asc",
) -> MeetingListResponse:
    """Returns a paginated, filtered list of meetings for the MeetingsPage."""
    repo = MeetingRepository()
    meetings, total = await repo.list_for_user(
        user_id=user_id,
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
    return MeetingListResponse(
        items=[_to_response(m) for m in meetings],
        total=total,
        page=page,
        page_size=page_size,
    )


async def get_meeting_by_id(user_id: str, meeting_id: str) -> MeetingResponse:
    """Returns a single meeting, scoped to the requesting user."""
    repo = MeetingRepository()
    meeting = await repo.get_for_user(user_id=user_id, meeting_id=meeting_id)
    if not meeting:
        raise AppException(status_code=404, detail="Meeting not found.")
    return _to_response(meeting)


async def create_meeting(user_id: str, payload: MeetingCreateRequest) -> MeetingResponse:
    """Creates a manually entered meeting."""
    user_repo = UserRepository()
    user = await user_repo.get_by_id(user_id)
    if not user:
        raise AppException(status_code=404, detail="User not found.")

    if payload.end_time <= payload.start_time:
        raise AppException(status_code=422, detail="end_time must be after start_time.")

    now = datetime.now(timezone.utc)
    meeting = MeetingModel(
        user_id=user.id,
        title=payload.title,
        start_time=payload.start_time,
        end_time=payload.end_time,
        description=payload.description,
        location=payload.location,
        attendees=payload.attendees,
        status="confirmed",
        source="manual",
        created_at=now,
        updated_at=now,
    )
    repo = MeetingRepository()
    saved = await repo.insert_one(meeting)
    logger.info("Meeting created: id=%s user_id=%s", saved.id, user_id)
    return _to_response(saved)


async def update_meeting(
    user_id: str, meeting_id: str, payload: MeetingUpdateRequest
) -> MeetingResponse:
    """Applies partial field updates to a meeting."""
    repo = MeetingRepository()
    meeting = await repo.get_for_user(user_id=user_id, meeting_id=meeting_id)
    if not meeting:
        raise AppException(status_code=404, detail="Meeting not found.")

    updates: dict = {"updated_at": datetime.now(timezone.utc)}
    if payload.title is not None:
        updates["title"] = payload.title
    if payload.start_time is not None:
        updates["start_time"] = payload.start_time
    if payload.end_time is not None:
        updates["end_time"] = payload.end_time
    if payload.description is not None:
        updates["description"] = payload.description
    if payload.location is not None:
        updates["location"] = payload.location
    if payload.attendees is not None:
        updates["attendees"] = payload.attendees

    # Validate time ordering if both are being updated
    new_start = updates.get("start_time", meeting.start_time)
    new_end = updates.get("end_time", meeting.end_time)
    if new_end <= new_start:
        raise AppException(status_code=422, detail="end_time must be after start_time.")

    updated = await repo.update_one(
        {"_id": meeting.id, "user_id": user_id},
        {"$set": updates},
    )
    if not updated:
        raise AppException(status_code=404, detail="Meeting not found.")
    return _to_response(updated)


async def update_meeting_status(
    user_id: str, meeting_id: str, status: str
) -> MeetingResponse:
    """Transitions a meeting's status (confirm, decline, etc.)."""
    if status not in VALID_STATUSES:
        raise AppException(
            status_code=422,
            detail=f"Invalid status '{status}'. Must be one of: {', '.join(VALID_STATUSES)}.",
        )

    repo = MeetingRepository()
    meeting = await repo.get_for_user(user_id=user_id, meeting_id=meeting_id)
    if not meeting:
        raise AppException(status_code=404, detail="Meeting not found.")

    updated = await repo.update_one(
        {"_id": meeting.id, "user_id": user_id},
        {"$set": {"status": status, "updated_at": datetime.now(timezone.utc)}},
    )
    if not updated:
        raise AppException(status_code=404, detail="Meeting not found.")
    return _to_response(updated)


async def delete_meeting(user_id: str, meeting_id: str) -> None:
    """Permanently removes a meeting document."""
    repo = MeetingRepository()
    deleted = await repo.delete_one({"user_id": user_id, "_id": meeting_id})
    if not deleted:
        raise AppException(status_code=404, detail="Meeting not found.")


async def get_upcoming_meetings(user_id: str, days: int = 7) -> list[MeetingResponse]:
    """
    Returns confirmed/detected meetings starting within the next `days`
    days. Used by the Dashboard's UpcomingMeetingsWidget.
    """
    now = datetime.now(timezone.utc)
    until = now + timedelta(days=days)
    repo = MeetingRepository()
    meetings = await repo.find_many(
        {
            "user_id": user_id,
            "start_time": {"$gte": now, "$lte": until},
            "status": {"$in": ["confirmed", "detected", "synced"]},
        },
        sort=[("start_time", 1)],
        limit=10,
    )
    return [_to_response(m) for m in meetings]


async def get_meeting_stats(user_id: str) -> MeetingStatsResponse:
    """
    Returns high-level meeting counts for the Dashboard StatCard
    and the MeetingsPage stats bar.
    """
    repo = MeetingRepository()
    total = await repo.count_documents({"user_id": user_id})
    pending = await repo.count_documents(
        {"user_id": user_id, "status": {"$in": ["detected", "confirmed"]}}
    )
    synced = await repo.count_documents({"user_id": user_id, "status": "synced"})

    return MeetingStatsResponse(
        total=total,
        pending_confirmation=pending,
        synced_to_calendar=synced,
    )

