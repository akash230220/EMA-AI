# backend/app/api/v1/endpoints/analytics.py
"""
Dashboard/Analytics metrics. Maps 1:1 to
frontend/src/api/analyticsApi.js.
"""

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse

from app.schemas.analytics_schema import (
    ActivityPointResponse,
    BreakdownEntryResponse,
    DashboardSummaryResponse,
    MonthlyTrendPointResponse,
    ResponseTimeAnalyticsResponse,
    AiTimeSavedResponse,
)
from app.services.analytics_service import (
    get_dashboard_summary,
    get_weekly_activity,
    get_monthly_trends,
    get_response_time_analytics,
    get_category_breakdown,
    get_priority_breakdown,
    get_sentiment_breakdown,
    get_intent_breakdown,
    get_ai_time_saved_breakdown,
    export_analytics_report,
)
from app.auth.jwt_handler import get_current_user

router = APIRouter()


@router.get("/summary", response_model=DashboardSummaryResponse)
async def summary(range: str = Query("30d", alias="range"), current_user=Depends(get_current_user)):
    return await get_dashboard_summary(user_id=current_user.id, range_=range)


@router.get("/weekly-activity", response_model=list[ActivityPointResponse])
async def weekly_activity(weeks: int = 1, current_user=Depends(get_current_user)):
    return await get_weekly_activity(user_id=current_user.id, weeks=weeks)


@router.get("/monthly-trends", response_model=list[MonthlyTrendPointResponse])
async def monthly_trends(months: int = 6, current_user=Depends(get_current_user)):
    return await get_monthly_trends(user_id=current_user.id, months=months)


@router.get("/response-time", response_model=ResponseTimeAnalyticsResponse)
async def response_time(range: str = "30d", current_user=Depends(get_current_user)):
    return await get_response_time_analytics(user_id=current_user.id, range_=range)


@router.get("/category-breakdown", response_model=list[BreakdownEntryResponse])
async def category_breakdown(range: str = "30d", current_user=Depends(get_current_user)):
    return await get_category_breakdown(user_id=current_user.id, range_=range)


@router.get("/priority-breakdown", response_model=list[BreakdownEntryResponse])
async def priority_breakdown(range: str = "30d", current_user=Depends(get_current_user)):
    return await get_priority_breakdown(user_id=current_user.id, range_=range)


@router.get("/sentiment-breakdown", response_model=list[BreakdownEntryResponse])
async def sentiment_breakdown(range: str = "30d", current_user=Depends(get_current_user)):
    return await get_sentiment_breakdown(user_id=current_user.id, range_=range)


@router.get("/intent-breakdown", response_model=list[BreakdownEntryResponse])
async def intent_breakdown(range: str = "30d", current_user=Depends(get_current_user)):
    return await get_intent_breakdown(user_id=current_user.id, range_=range)


@router.get("/ai-time-saved", response_model=AiTimeSavedResponse)
async def ai_time_saved(range: str = "30d", current_user=Depends(get_current_user)):
    return await get_ai_time_saved_breakdown(user_id=current_user.id, range_=range)


@router.get("/export")
async def export_report(range: str = "30d", format: str = "csv", current_user=Depends(get_current_user)):
    """Returns a downloadable CSV/PDF report — matches emailApi's blob responseType expectation."""
    file_bytes, media_type, filename = await export_analytics_report(
        user_id=current_user.id, range_=range, format_=format
    )
    return StreamingResponse(
        iter([file_bytes]),
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )