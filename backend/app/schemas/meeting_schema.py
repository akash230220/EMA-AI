# backend/app/schemas/meeting_schema.py
from datetime import datetime
from typing import Optional

from pydantic import Field

from app.schemas.common_schema import CamelModel


# ---------------------------------------------------------------------------
# Requests
# ---------------------------------------------------------------------------

class MeetingCreateRequest(CamelModel):
    title: str
    start_time: datetime
    end_time: datetime
    description: Optional[str] = None
    location: Optional[str] = None
    attendees: list[str] = Field(default_factory=list)


class MeetingUpdateRequest(CamelModel):
    title: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    description: Optional[str] = None
    location: Optional[str] = None
    attendees: Optional[list[str]] = None


class MeetingStatusUpdateRequest(CamelModel):
    status: str  # detected | confirmed | declined | synced


# ---------------------------------------------------------------------------
# Responses
# ---------------------------------------------------------------------------

class DateShortLabel(CamelModel):
    month: str
    day: str


class MeetingResponse(CamelModel):
    id: str
    title: str
    start_time: datetime
    end_time: datetime
    start_time_label: str
    end_time_label: str
    date_short_label: Optional[DateShortLabel] = None
    date_group_label: Optional[str] = None
    location: Optional[str] = None
    description: Optional[str] = None
    attendees: list[str] = Field(default_factory=list)
    status: str
    source: str  # ai_detected | manual
    source_email_id: Optional[str] = None
    calendar_event_id: Optional[str] = None


class MeetingListResponse(CamelModel):
    items: list[MeetingResponse]
    total: int
    page: int
    page_size: int


class MeetingStatsResponse(CamelModel):
    total: int
    pending_confirmation: int
    synced_to_calendar: int