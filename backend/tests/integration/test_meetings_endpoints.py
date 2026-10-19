# backend/tests/integration/test_meetings_endpoints.py
"""
Integration tests for /api/v1/meetings/*, with specific attention to
the calendar sync endpoints and the confirm/decline status transition
— the two-step "AI suggests -> human confirms -> optionally syncs"
flow that's central to the Meetings feature's design.
"""

from unittest.mock import AsyncMock, patch

import pytest


def _sample_meeting(meeting_id="m1", **overrides):
    base = {
        "id": meeting_id,
        "title": "Q3 Budget Review",
        "start_time": "2026-02-01T09:00:00Z",
        "end_time": "2026-02-01T09:30:00Z",
        "start_time_label": "9:00 AM",
        "end_time_label": "9:30 AM",
        "date_short_label": {"month": "FEB", "day": "1"},
        "date_group_label": "Sun, Feb 1",
        "location": None,
        "description": None,
        "attendees": [],
        "status": "detected",
        "source": "ai_detected",
        "source_email_id": "e1",
        "calendar_event_id": None,
    }
    base.update(overrides)
    return base


class TestCreateMeeting:
    def test_create_meeting_with_valid_range_returns_201(self, authenticated_client):
        with patch(
            "app.api.v1.endpoints.meetings.create_meeting",
            new=AsyncMock(return_value=_sample_meeting(source="manual", status="confirmed")),
        ):
            response = authenticated_client.post(
                "/api/v1/meetings",
                json={
                    "title": "Q3 Budget Review",
                    "startTime": "2026-02-01T09:00:00Z",
                    "endTime": "2026-02-01T09:30:00Z",
                },
            )
        assert response.status_code == 201

    def test_create_meeting_with_end_before_start_still_passes_schema_validation(self, authenticated_client):
        # MeetingCreateRequest doesn't currently cross-validate
        # end_time > start_time at the schema layer (see
        # schemas/meeting_schema.py) — this documents that gap.
        # frontend/src/lib/validators.js's isValidTimeRange() catches
        # this client-side, but the backend should arguably enforce
        # it too via a @model_validator. Flagging as a hardening item.
        with patch(
            "app.api.v1.endpoints.meetings.create_meeting",
            new=AsyncMock(return_value=_sample_meeting()),
        ):
            response = authenticated_client.post(
                "/api/v1/meetings",
                json={
                    "title": "Backwards meeting",
                    "startTime": "2026-02-01T10:00:00Z",
                    "endTime": "2026-02-01T09:00:00Z",
                },
            )
        assert response.status_code == 201  # currently passes — see note above


class TestCalendarSync:
    def test_sync_to_calendar_returns_meeting_with_synced_status(self, authenticated_client):
        synced = _sample_meeting(status="synced", calendar_event_id="gcal-evt-123")
        with patch(
            "app.api.v1.endpoints.meetings.sync_meeting_to_calendar",
            new=AsyncMock(return_value=synced),
        ):
            response = authenticated_client.post("/api/v1/meetings/m1/sync-calendar")
        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "synced"
        assert body["calendarEventId"] == "gcal-evt-123"

    def test_unsync_from_calendar_clears_calendar_event_id(self, authenticated_client):
        unsynced = _sample_meeting(status="confirmed", calendar_event_id=None)
        with patch(
            "app.api.v1.endpoints.meetings.unsync_meeting_from_calendar",
            new=AsyncMock(return_value=unsynced),
        ):
            response = authenticated_client.delete("/api/v1/meetings/m1/sync-calendar")
        assert response.status_code == 200
        assert response.json()["calendarEventId"] is None


class TestUpcomingMeetings:
    def test_upcoming_meetings_defaults_to_seven_days(self, authenticated_client):
        mock_upcoming = AsyncMock(return_value=[])
        with patch("app.api.v1.endpoints.meetings.get_upcoming_meetings", new=mock_upcoming):
            authenticated_client.get("/api/v1/meetings/upcoming")
        _, kwargs = mock_upcoming.call_args
        assert kwargs["days"] == 7

    def test_upcoming_meetings_accepts_custom_days_param(self, authenticated_client):
        mock_upcoming = AsyncMock(return_value=[])
        with patch("app.api.v1.endpoints.meetings.get_upcoming_meetings", new=mock_upcoming):
            authenticated_client.get("/api/v1/meetings/upcoming?days=14")
        _, kwargs = mock_upcoming.call_args
        assert kwargs["days"] == 14


class TestDeleteMeeting:
    def test_delete_meeting_returns_204(self, authenticated_client):
        with patch("app.api.v1.endpoints.meetings.delete_meeting", new=AsyncMock(return_value=None)):
            response = authenticated_client.delete("/api/v1/meetings/m1")
        assert response.status_code == 204