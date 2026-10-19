# backend/app/utils/datetime_utils.py
"""
Datetime and Timezone Utility Helpers.

Responsibilities:
  - Timezone-aware UTC timestamp generation (utcnow)
  - ISO-8601 parsing & formatting
  - Human-friendly relative date/time label generation for UI cards
  - Date range calculator for analytics reporting (7d, 30d, 90d, 1y)
"""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from typing import Optional


def utcnow() -> datetime:
    """Returns the current timezone-aware UTC datetime."""
    return datetime.now(timezone.utc)


def parse_iso_datetime(dt_str: Optional[str]) -> Optional[datetime]:
    """Parses an ISO 8601 string into a timezone-aware UTC datetime."""
    if not dt_str:
        return None
    try:
        cleaned = dt_str.replace("Z", "+00:00")
        dt = datetime.fromisoformat(cleaned)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except Exception:
        return None


def format_datetime_label(dt: Optional[datetime]) -> str:
    """
    Formats a datetime into a human-friendly label.
    e.g., 'Aug 26, 2026 10:30 AM' or 'Today at 10:30 AM'
    """
    if dt is None:
        return ""

    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)

    now = datetime.now(timezone.utc)
    diff = now - dt

    if diff.total_seconds() < 60:
        return "Just now"
    if diff.total_seconds() < 3600:
        mins = int(diff.total_seconds() / 60)
        return f"{mins}m ago"
    if diff.days == 0 and dt.date() == now.date():
        return dt.strftime("Today at %I:%M %p")
    if diff.days == 1:
        return dt.strftime("Yesterday at %I:%M %p")

    if dt.year == now.year:
        return dt.strftime("%b %d, %I:%M %p")
    return dt.strftime("%b %d, %Y %I:%M %p")


def format_date_label(d: Optional[date | datetime]) -> str:
    """Formats a date into a human-readable string like 'Aug 26, 2026'."""
    if d is None:
        return ""
    if isinstance(d, datetime):
        d = d.date()

    today = date.today()
    if d == today:
        return "Today"
    if (d - today).days == 1:
        return "Tomorrow"
    if (today - d).days == 1:
        return "Yesterday"

    if d.year == today.year:
        return d.strftime("%b %d")
    return d.strftime("%b %d, %Y")


def parse_date_range(range_str: str) -> tuple[date, date]:
    """
    Calculates start and end dates for a range identifier ('7d', '30d', '90d', '1y').
    """
    today = date.today()
    mapping = {
        "7d": 7,
        "30d": 30,
        "90d": 90,
        "180d": 180,
        "1y": 365,
    }
    days = mapping.get(range_str.lower(), 30)
    start_date = today - timedelta(days=days - 1)
    return start_date, today
