# backend/app/services/analytics_service.py
"""
Analytics service — dashboard metrics, charts, breakdowns, and export.

Data strategy:
  - Pre-aggregated daily AnalyticsSnapshotModel documents are the
    primary source (populated by tasks/scheduler.py's nightly job).
  - For the current day (not yet snapshotted), we fall back to
    live aggregation queries against the emails/tasks/meetings
    collections. This keeps chart queries fast even as email volume
    grows large, while ensuring the dashboard is always up-to-date.

All snapshot Mongo I/O goes through AnalyticsSnapshotRepository.
Live aggregation queries run directly on the Motor collection.
"""

from __future__ import annotations

import csv
import io
import logging
from datetime import date, datetime, timedelta, timezone
from typing import Optional

from app.db.mongo_client import get_database
from app.exceptions.custom_exceptions import AppException
from app.repositories.analytics_repository import AnalyticsSnapshotRepository
from app.schemas.analytics_schema import (
    ActivityPointResponse,
    AiTimeSavedBreakdownEntryResponse,
    AiTimeSavedResponse,
    BreakdownEntryResponse,
    DashboardSummaryResponse,
    MonthlyTrendPointResponse,
    ResponseTimeAnalyticsResponse,
    ResponseTimeByPriorityResponse,
    ResponseTimeTrendPointResponse,
)

logger = logging.getLogger("ai_email_os.analytics_service")

# ------------------------------------------------------------------
# Estimated AI time savings (minutes) per action — used for the
# AiTimeSavedPanel and the Dashboard StatCard.
# ------------------------------------------------------------------
TIME_SAVED_ESTIMATES = {
    "email_categorization": 0.5,
    "ai_reply_generated": 3.0,
    "meeting_detected": 2.0,
    "task_extracted": 1.5,
    "email_summarized": 1.0,
}


def _parse_range(range_: str) -> tuple[date, date]:
    """Parse range strings like '7d', '30d', '90d', '1y' into (start_date, end_date)."""
    today = date.today()
    mapping = {
        "7d": 7,
        "30d": 30,
        "90d": 90,
        "180d": 180,
        "1y": 365,
    }
    days = mapping.get(range_, 30)
    return today - timedelta(days=days - 1), today


async def _live_email_counts(user_id: str) -> dict:
    """Aggregate live counts directly from the emails collection."""
    db = get_database()
    col = db["emails"]
    pipeline = [
        {"$match": {"user_id": user_id, "deleted": {"$ne": True}}},
        {
            "$group": {
                "_id": None,
                "total": {"$sum": 1},
                "high_priority": {"$sum": {"$cond": [{"$eq": ["$priority", "high"]}, 1, 0]}},
                "pending_reply": {"$sum": {"$cond": ["$pending_reply", 1, 0]}},
            }
        },
    ]
    result = await col.aggregate(pipeline).to_list(1)
    if result:
        return result[0]
    return {"total": 0, "high_priority": 0, "pending_reply": 0}


async def get_dashboard_summary(
    user_id: str, range_: str = "30d"
) -> DashboardSummaryResponse:
    """
    Returns the Dashboard StatCardGrid metrics. Uses pre-aggregated
    snapshots for historical sums + live queries for real-time counts.
    """
    start, end = _parse_range(range_)
    snap_repo = AnalyticsSnapshotRepository()
    snapshots = await snap_repo.list_for_user_range(user_id, start, end)

    total_emails = sum(s.emails_received for s in snapshots)
    high_priority = sum(s.high_priority_emails for s in snapshots)
    ai_replies = sum(s.ai_replies_generated for s in snapshots)
    ai_time_saved = sum(s.ai_time_saved_minutes for s in snapshots)

    # Live queries for real-time stats
    db = get_database()
    pending_replies = await db["emails"].count_documents(
        {"user_id": user_id, "pending_reply": True, "deleted": {"$ne": True}}
    )
    meetings = await db["meetings"].count_documents({"user_id": user_id})
    tasks = await db["tasks"].count_documents({"user_id": user_id})

    # Average response time from snapshots that have it
    response_times = [s.avg_response_time_minutes for s in snapshots if s.avg_response_time_minutes is not None]
    avg_response = sum(response_times) / len(response_times) if response_times else None

    return DashboardSummaryResponse(
        total_emails=total_emails,
        high_priority_emails=high_priority,
        pending_replies=pending_replies,
        meetings=meetings,
        tasks=tasks,
        ai_replies_generated=ai_replies,
        ai_time_saved_minutes=round(ai_time_saved, 1),
        avg_response_time_minutes=round(avg_response, 1) if avg_response else None,
    )


async def get_weekly_activity(
    user_id: str, weeks: int = 1
) -> list[ActivityPointResponse]:
    """
    Returns day-by-day email received/replied counts for the last
    `weeks` × 7 days. Powers the WeeklyActivityChart on the Dashboard.
    """
    days = weeks * 7
    start, end = date.today() - timedelta(days=days - 1), date.today()
    snap_repo = AnalyticsSnapshotRepository()
    snapshots = await snap_repo.list_for_user_range(user_id, start, end)
    snap_by_date = {s.snapshot_date: s for s in snapshots}

    result: list[ActivityPointResponse] = []
    for i in range(days):
        d = start + timedelta(days=i)
        snap = snap_by_date.get(d)
        result.append(
            ActivityPointResponse(
                date=d.isoformat(),
                received=snap.emails_received if snap else 0,
                replied=snap.emails_replied if snap else 0,
            )
        )
    return result


async def get_monthly_trends(
    user_id: str, months: int = 6
) -> list[MonthlyTrendPointResponse]:
    """
    Returns month-level email, AI reply, and time-saved totals.
    Powers the MonthlyTrendChart on the AnalyticsPage.
    """
    today = date.today()
    result: list[MonthlyTrendPointResponse] = []
    snap_repo = AnalyticsSnapshotRepository()

    for offset in range(months - 1, -1, -1):
        # First day of the month (months ago)
        month_start = (today.replace(day=1) - timedelta(days=offset * 28)).replace(day=1)
        # Last day of that month
        if month_start.month == 12:
            month_end = month_start.replace(year=month_start.year + 1, month=1) - timedelta(days=1)
        else:
            month_end = month_start.replace(month=month_start.month + 1) - timedelta(days=1)

        snapshots = await snap_repo.list_for_user_range(user_id, month_start, month_end)
        result.append(
            MonthlyTrendPointResponse(
                month=month_start.strftime("%b %Y"),
                total_emails=sum(s.emails_received for s in snapshots),
                ai_replies=sum(s.ai_replies_generated for s in snapshots),
                time_saved_minutes=round(sum(s.ai_time_saved_minutes for s in snapshots), 1),
            )
        )
    return result


async def get_response_time_analytics(
    user_id: str, range_: str = "30d"
) -> ResponseTimeAnalyticsResponse:
    """
    Returns average response times overall, by priority, and as a
    daily trend. Powers the ResponseTimeAnalyticsChart.
    """
    start, end = _parse_range(range_)
    snap_repo = AnalyticsSnapshotRepository()
    snapshots = await snap_repo.list_for_user_range(user_id, start, end)

    valid_times = [s.avg_response_time_minutes for s in snapshots if s.avg_response_time_minutes is not None]
    overall_avg = sum(valid_times) / len(valid_times) if valid_times else 0.0

    # Live breakdown by priority from the emails collection
    db = get_database()
    pipeline = [
        {
            "$match": {
                "user_id": user_id,
                "replied_at": {"$exists": True, "$ne": None},
                "received_at": {"$exists": True},
            }
        },
        {
            "$project": {
                "priority": 1,
                "response_minutes": {
                    "$divide": [
                        {"$subtract": ["$replied_at", "$received_at"]},
                        60000,  # ms -> minutes
                    ]
                },
            }
        },
        {"$group": {"_id": "$priority", "avg_minutes": {"$avg": "$response_minutes"}}},
    ]
    priority_docs = await db["emails"].aggregate(pipeline).to_list(10)
    by_priority = [
        ResponseTimeByPriorityResponse(
            priority=doc["_id"] or "unknown",
            avg_minutes=round(doc["avg_minutes"], 1),
        )
        for doc in priority_docs
        if doc["_id"]
    ]

    # Daily trend from snapshots
    trend = [
        ResponseTimeTrendPointResponse(
            date=s.snapshot_date.isoformat(),
            avg_minutes=round(s.avg_response_time_minutes, 1),
        )
        for s in snapshots
        if s.avg_response_time_minutes is not None
    ]

    return ResponseTimeAnalyticsResponse(
        average_response_time_minutes=round(overall_avg, 1),
        by_priority=by_priority,
        trend=trend,
    )


async def _get_breakdown(
    user_id: str, field: str, range_: str
) -> list[BreakdownEntryResponse]:
    """Generic breakdown aggregation (category / priority / sentiment / intent)."""
    start, end = _parse_range(range_)
    snap_repo = AnalyticsSnapshotRepository()
    snapshots = await snap_repo.list_for_user_range(user_id, start, end)

    # Sum the per-snapshot dicts for the requested field
    counts_attr = f"{field}_counts"
    totals: dict[str, int] = {}
    for snap in snapshots:
        field_data: dict = getattr(snap, counts_attr, {})
        for key, cnt in field_data.items():
            totals[key] = totals.get(key, 0) + cnt

    grand_total = sum(totals.values()) or 1
    return [
        BreakdownEntryResponse(
            category=k,
            count=v,
            percentage=round(v / grand_total * 100, 1),
        )
        for k, v in sorted(totals.items(), key=lambda x: x[1], reverse=True)
    ]


async def get_category_breakdown(user_id: str, range_: str = "30d") -> list[BreakdownEntryResponse]:
    return await _get_breakdown(user_id, "category", range_)


async def get_priority_breakdown(user_id: str, range_: str = "30d") -> list[BreakdownEntryResponse]:
    return await _get_breakdown(user_id, "priority", range_)


async def get_sentiment_breakdown(user_id: str, range_: str = "30d") -> list[BreakdownEntryResponse]:
    return await _get_breakdown(user_id, "sentiment", range_)


async def get_intent_breakdown(user_id: str, range_: str = "30d") -> list[BreakdownEntryResponse]:
    return await _get_breakdown(user_id, "intent", range_)


async def get_ai_time_saved_breakdown(
    user_id: str, range_: str = "30d"
) -> AiTimeSavedResponse:
    """
    Returns total AI time saved and per-activity breakdown.
    Powers the AiTimeSavedPanel on the Dashboard.
    """
    start, end = _parse_range(range_)
    snap_repo = AnalyticsSnapshotRepository()
    snapshots = await snap_repo.list_for_user_range(user_id, start, end)

    totals: dict[str, float] = {}
    for snap in snapshots:
        for activity, minutes in snap.ai_time_saved_breakdown.items():
            totals[activity] = totals.get(activity, 0.0) + minutes

    grand_total = sum(totals.values())
    breakdown = [
        AiTimeSavedBreakdownEntryResponse(
            activity=k,
            minutes_saved=round(v, 1),
        )
        for k, v in sorted(totals.items(), key=lambda x: x[1], reverse=True)
    ]

    return AiTimeSavedResponse(
        total_minutes_saved=round(grand_total, 1),
        breakdown=breakdown,
    )


async def export_analytics_report(
    user_id: str, range_: str = "30d", format_: str = "csv"
) -> tuple[bytes, str, str]:
    """
    Generates a downloadable analytics report.
    Returns (file_bytes, media_type, filename).
    Currently supports CSV; PDF support can be added later.
    """
    start, end = _parse_range(range_)
    snap_repo = AnalyticsSnapshotRepository()
    snapshots = await snap_repo.list_for_user_range(user_id, start, end)

    if format_ == "csv":
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow([
            "date", "emails_received", "emails_replied",
            "high_priority", "ai_replies", "meetings_detected",
            "tasks_extracted", "ai_time_saved_minutes",
        ])
        for s in snapshots:
            writer.writerow([
                s.snapshot_date.isoformat(),
                s.emails_received,
                s.emails_replied,
                s.high_priority_emails,
                s.ai_replies_generated,
                s.meetings_detected,
                s.tasks_extracted,
                round(s.ai_time_saved_minutes, 2),
            ])
        file_bytes = output.getvalue().encode()
        filename = f"analytics_{range_}_{date.today().isoformat()}.csv"
        return file_bytes, "text/csv", filename

    raise AppException(status_code=422, detail=f"Unsupported export format: '{format_}'. Use 'csv'.")

