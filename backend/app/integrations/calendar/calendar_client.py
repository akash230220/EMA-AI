# backend/app/integrations/calendar/calendar_client.py
"""
Google Calendar API Client and Meeting Sync.

Responsibilities:
  - GoogleCalendarClient: Direct async HTTP wrapper for Google Calendar REST API (v3)
  - sync_meeting_to_calendar: Pushes local MeetingModel to Google Calendar & marks synced
  - unsync_meeting_from_calendar: Deletes event on Google Calendar & resets local status
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Optional

import httpx

from app.exceptions.custom_exceptions import AppException
from app.integrations.gmail.gmail_client import ensure_valid_token
from app.models.meeting import MeetingModel
from app.models.user import GoogleOAuthTokens
from app.repositories.meeting_repository import MeetingRepository
from app.repositories.user_repository import UserRepository
from app.schemas.meeting_schema import DateShortLabel, MeetingResponse
from app.utils.datetime_utils import format_datetime_label

logger = logging.getLogger("ai_email_os.calendar_client")

CALENDAR_API_BASE = "https://www.googleapis.com/calendar/v3/calendars/primary/events"


class GoogleCalendarClient:
    """Async client wrapper for Google Calendar v3 REST API operations."""

    def __init__(self, oauth_tokens: GoogleOAuthTokens):
        self.oauth_tokens = oauth_tokens

    async def _get_headers(self) -> dict[str, str]:
        token = await ensure_valid_token(self.oauth_tokens)
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

    async def create_event(
        self,
        summary: str,
        start_time: datetime,
        end_time: datetime,
        description: Optional[str] = None,
        location: Optional[str] = None,
        attendees: Optional[list[str]] = None,
        user_timezone: str = "UTC",
    ) -> dict[str, Any]:
        """
        Creates an event on the user's primary Google Calendar.
        Calls POST /calendars/primary/events
        """
        headers = await self._get_headers()

        # Ensure timezone-aware ISO strings
        start_iso = start_time.isoformat() if start_time.tzinfo else start_time.replace(tzinfo=timezone.utc).isoformat()
        end_iso = end_time.isoformat() if end_time.tzinfo else end_time.replace(tzinfo=timezone.utc).isoformat()

        payload: dict[str, Any] = {
            "summary": summary,
            "start": {"dateTime": start_iso, "timeZone": user_timezone},
            "end": {"dateTime": end_iso, "timeZone": user_timezone},
        }

        if description:
            payload["description"] = description
        if location:
            payload["location"] = location
        if attendees:
            payload["attendees"] = [{"email": addr.strip()} for addr in attendees if addr.strip()]

        async with httpx.AsyncClient(timeout=20.0) as client:
            resp = await client.post(CALENDAR_API_BASE, headers=headers, json=payload)

        if resp.status_code not in (200, 201):
            logger.error("Failed to create Google Calendar event (%s): %s", resp.status_code, resp.text)
            raise ValueError(f"Google Calendar event creation failed: {resp.text}")

        event_data = resp.json()
        logger.info("Successfully created Google Calendar event: id=%s", event_data.get("id"))
        return event_data

    async def update_event(
        self,
        event_id: str,
        summary: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        description: Optional[str] = None,
        location: Optional[str] = None,
        attendees: Optional[list[str]] = None,
        user_timezone: str = "UTC",
    ) -> dict[str, Any]:
        """Calls PATCH /calendars/primary/events/{eventId}."""
        headers = await self._get_headers()
        payload: dict[str, Any] = {}

        if summary is not None:
            payload["summary"] = summary
        if start_time is not None:
            start_iso = start_time.isoformat() if start_time.tzinfo else start_time.replace(tzinfo=timezone.utc).isoformat()
            payload["start"] = {"dateTime": start_iso, "timeZone": user_timezone}
        if end_time is not None:
            end_iso = end_time.isoformat() if end_time.tzinfo else end_time.replace(tzinfo=timezone.utc).isoformat()
            payload["end"] = {"dateTime": end_iso, "timeZone": user_timezone}
        if description is not None:
            payload["description"] = description
        if location is not None:
            payload["location"] = location
        if attendees is not None:
            payload["attendees"] = [{"email": addr.strip()} for addr in attendees if addr.strip()]

        async with httpx.AsyncClient(timeout=20.0) as client:
            resp = await client.patch(f"{CALENDAR_API_BASE}/{event_id}", headers=headers, json=payload)

        if resp.status_code != 200:
            logger.error("Failed to update Google Calendar event %s (%s): %s", event_id, resp.status_code, resp.text)
            raise ValueError(f"Google Calendar event update failed: {resp.text}")

        return resp.json()

    async def delete_event(self, event_id: str) -> bool:
        """Calls DELETE /calendars/primary/events/{eventId}."""
        headers = await self._get_headers()
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.delete(f"{CALENDAR_API_BASE}/{event_id}", headers=headers)

        if resp.status_code in (200, 204, 410):
            logger.info("Successfully deleted Google Calendar event: %s", event_id)
            return True
        elif resp.status_code == 404:
            logger.warning("Google Calendar event %s not found on remote; treating as deleted.", event_id)
            return True
        else:
            logger.error("Failed to delete Google Calendar event %s (%s): %s", event_id, resp.status_code, resp.text)
            raise ValueError(f"Google Calendar event deletion failed: {resp.text}")

    async def get_event(self, event_id: str) -> dict[str, Any]:
        """Calls GET /calendars/primary/events/{eventId}."""
        headers = await self._get_headers()
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(f"{CALENDAR_API_BASE}/{event_id}", headers=headers)

        if resp.status_code != 200:
            logger.error("Failed to fetch Google Calendar event %s (%s): %s", event_id, resp.status_code, resp.text)
            raise ValueError(f"Google Calendar event lookup failed: {resp.text}")

        return resp.json()


# ---------------------------------------------------------------------------
# High-level Sync Functions
# ---------------------------------------------------------------------------

def _meeting_to_response(meeting: MeetingModel) -> MeetingResponse:
    return MeetingResponse(
        id=str(meeting.id),
        title=meeting.title,
        start_time=meeting.start_time,
        end_time=meeting.end_time,
        start_time_label=format_datetime_label(meeting.start_time),
        end_time_label=format_datetime_label(meeting.end_time),
        date_short_label=DateShortLabel(
            month=meeting.start_time.strftime("%b"),
            day=meeting.start_time.strftime("%d").lstrip("0"),
        ),
        date_group_label=meeting.start_time.strftime("%-d %b %Y"),
        location=meeting.location,
        description=meeting.description,
        attendees=meeting.attendees,
        status=meeting.status,
        source=meeting.source,
        source_email_id=str(meeting.source_email_id) if meeting.source_email_id else None,
        calendar_event_id=meeting.calendar_event_id,
    )


async def sync_meeting_to_calendar(user_id: str, meeting_id: str) -> MeetingResponse:
    """
    Pushes a detected or confirmed meeting to Google Calendar via Calendar API.
    Updates meeting record with status='synced' and calendar_event_id.
    """
    meeting_repo = MeetingRepository()
    meeting = await meeting_repo.get_for_user(user_id=user_id, meeting_id=meeting_id)
    if not meeting:
        raise AppException(status_code=404, detail="Meeting not found.")

    user_repo = UserRepository()
    user = await user_repo.get_by_id(user_id)
    if not user or not user.oauth_tokens or not user.oauth_tokens.calendar_connected:
        raise AppException(status_code=400, detail="Google Calendar is not connected.")

    client = GoogleCalendarClient(user.oauth_tokens)

    try:
        if meeting.calendar_event_id:
            # Already has a calendar event — update it
            event = await client.update_event(
                event_id=meeting.calendar_event_id,
                summary=meeting.title,
                start_time=meeting.start_time,
                end_time=meeting.end_time,
                description=meeting.description,
                location=meeting.location,
                attendees=meeting.attendees,
                user_timezone=user.timezone,
            )
            event_id = event["id"]
        else:
            # Create new calendar event
            event = await client.create_event(
                summary=meeting.title,
                start_time=meeting.start_time,
                end_time=meeting.end_time,
                description=meeting.description,
                location=meeting.location,
                attendees=meeting.attendees,
                user_timezone=user.timezone,
            )
            event_id = event["id"]
    except Exception as exc:
        logger.exception("Failed to sync meeting %s to Google Calendar: %s", meeting_id, exc)
        raise AppException(status_code=500, detail=f"Google Calendar sync failed: {str(exc)}") from exc

    now = datetime.now(timezone.utc)
    updated = await meeting_repo.update_one(
        {"_id": meeting.id, "user_id": user_id},
        {
            "$set": {
                "status": "synced",
                "calendar_event_id": event_id,
                "updated_at": now,
            }
        },
    )

    # Update user's last_calendar_synced_at
    await user_repo.update_one(
        {"_id": user.id},
        {"$set": {"oauth_tokens.last_calendar_synced_at": now, "updated_at": now}},
    )

    logger.info("Meeting %s synced to Google Calendar (event_id=%s)", meeting_id, event_id)
    return _meeting_to_response(updated or meeting)


async def unsync_meeting_from_calendar(user_id: str, meeting_id: str) -> MeetingResponse:
    """
    Deletes the corresponding event from Google Calendar and resets the
    local meeting status to 'confirmed'.
    """
    meeting_repo = MeetingRepository()
    meeting = await meeting_repo.get_for_user(user_id=user_id, meeting_id=meeting_id)
    if not meeting:
        raise AppException(status_code=404, detail="Meeting not found.")

    if meeting.calendar_event_id:
        user_repo = UserRepository()
        user = await user_repo.get_by_id(user_id)
        if user and user.oauth_tokens:
            try:
                client = GoogleCalendarClient(user.oauth_tokens)
                await client.delete_event(meeting.calendar_event_id)
            except Exception as exc:
                logger.warning("Failed to delete event from Google Calendar during unsync: %s", exc)

    now = datetime.now(timezone.utc)
    updated = await meeting_repo.update_one(
        {"_id": meeting.id, "user_id": user_id},
        {
            "$set": {
                "status": "confirmed",
                "calendar_event_id": None,
                "updated_at": now,
            }
        },
    )
    logger.info("Meeting %s unsynced from Google Calendar", meeting_id)
    return _meeting_to_response(updated or meeting)

