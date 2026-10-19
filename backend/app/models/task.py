# backend/app/models/task.py
"""Task document — AI-extracted or manually created action items."""

from datetime import date, datetime
from typing import Optional

from pydantic import Field

from app.models.base import MongoBaseModel, PyObjectId, utcnow


class TaskModel(MongoBaseModel):
    """Collection: `tasks`"""

    user_id: PyObjectId
    title: str
    description: Optional[str] = None
    due_date: Optional[date] = None
    priority: Optional[str] = None  # high | medium | low

    status: str = "pending"  # pending | in_progress | completed | dismissed
    source: str = "manual"  # ai_extracted | manual
    source_email_id: Optional[PyObjectId] = None

    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)
    completed_at: Optional[datetime] = None