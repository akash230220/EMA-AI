# backend/app/models/analytics_snapshot.py
"""
Analytics snapshot document — pre-aggregated daily rollups, computed
by a scheduled job (tasks/scheduler.py) rather than aggregating raw
email documents on every dashboard request. Keeps AnalyticsPage's
6+ chart queries fast even as the emails collection grows large.
"""

from datetime import date, datetime
from typing import Optional

from pydantic import Field

from app.models.base import MongoBaseModel, PyObjectId, utcnow


class AnalyticsSnapshotModel(MongoBaseModel):
    """
    Collection: `analytics_snapshots` — one document per (user_id,
    snapshot_date). Populated by a nightly aggregation job; analytics
    endpoints query a date range of these rather than scanning
    emails/tasks/meetings directly for every request.
    """

    user_id: PyObjectId
    snapshot_date: date

    total_emails: int = 0
    emails_received: int = 0
    emails_replied: int = 0
    high_priority_emails: int = 0

    category_counts: dict[str, int] = Field(default_factory=dict)
    priority_counts: dict[str, int] = Field(default_factory=dict)
    sentiment_counts: dict[str, int] = Field(default_factory=dict)
    intent_counts: dict[str, int] = Field(default_factory=dict)

    meetings_detected: int = 0
    tasks_extracted: int = 0
    ai_replies_generated: int = 0

    avg_response_time_minutes: Optional[float] = None
    ai_time_saved_minutes: float = 0
    ai_time_saved_breakdown: dict[str, float] = Field(default_factory=dict)

    created_at: datetime = Field(default_factory=utcnow)