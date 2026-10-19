# backend/app/models/meeting.py
"""Meeting document — AI-detected or manually created calendar events."""

from datetime import datetime
from typing import Optional

from pydantic import Field

from app.models.base import MongoBaseModel, PyObjectId, utcnow


class MeetingModel(MongoBaseModel):
    """Collection: `meetings`"""

    user_id: PyObjectId
    title: str
    description: Optional[str] = None
    location: Optional[str] = None
    attendees: list[str] = Field(default_factory=list)  # email addresses

    start_time: datetime
    end_time: datetime

    status: str = "detected"  # detected | confirmed | declined | synced
    source: str = "manual"  # ai_detected | manual
    source_email_id: Optional[PyObjectId] = None

    calendar_event_id: Optional[str] = Field(
        default=None, description="Google Calendar event id, set once synced."
    )

    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)