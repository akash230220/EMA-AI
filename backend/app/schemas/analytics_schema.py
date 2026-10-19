# backend/app/schemas/analytics_schema.py
from typing import Optional

from app.schemas.common_schema import CamelModel


class DashboardSummaryResponse(CamelModel):
    total_emails: int
    high_priority_emails: int
    pending_replies: int
    meetings: int
    tasks: int
    ai_replies_generated: int
    ai_time_saved_minutes: float
    avg_response_time_minutes: Optional[float] = None


class ActivityPointResponse(CamelModel):
    date: str
    received: int
    replied: int


class MonthlyTrendPointResponse(CamelModel):
    month: str
    total_emails: int
    ai_replies: int
    time_saved_minutes: float


class BreakdownEntryResponse(CamelModel):
    category: str  # generic key name — reused for priority/sentiment/intent breakdowns too
    count: int
    percentage: float


class ResponseTimeByPriorityResponse(CamelModel):
    priority: str
    avg_minutes: float


class ResponseTimeTrendPointResponse(CamelModel):
    date: str
    avg_minutes: float


class ResponseTimeAnalyticsResponse(CamelModel):
    average_response_time_minutes: float
    by_priority: list[ResponseTimeByPriorityResponse]
    trend: list[ResponseTimeTrendPointResponse]


class AiTimeSavedBreakdownEntryResponse(CamelModel):
    activity: str
    minutes_saved: float


class AiTimeSavedResponse(CamelModel):
    total_minutes_saved: float
    breakdown: list[AiTimeSavedBreakdownEntryResponse]