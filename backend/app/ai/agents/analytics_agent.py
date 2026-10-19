# backend/app/ai/agents/analytics_agent.py
"""
Analytics Agent.

Computes daily analytics snapshots and generates executive daily briefing summaries.
"""

from __future__ import annotations

import logging
from datetime import date, datetime, timedelta, timezone
from typing import Any

from app.ai.gemini.gemini_client import get_gemini_client
from app.ai.prompts.prompt_library import DAILY_BRIEF_SYSTEM_PROMPT
from app.db.mongo_client import get_database
from app.models.analytics_snapshot import AnalyticsSnapshotModel
from app.repositories.analytics_repository import AnalyticsSnapshotRepository

logger = logging.getLogger("ai_email_os.analytics_agent")


async def generate_daily_snapshot(user_id: str, target_date: date) -> AnalyticsSnapshotModel:
    """
    Rolls up email, task, and meeting activity for a given day into an AnalyticsSnapshotModel.
    """
    db = get_database()
    start_dt = datetime.combine(target_date, datetime.min.time()).replace(tzinfo=timezone.utc)
    end_dt = datetime.combine(target_date, datetime.max.time()).replace(tzinfo=timezone.utc)

    # 1. Email counts for the day
    email_pipeline = [
        {
            "$match": {
                "user_id": user_id,
                "received_at": {"$gte": start_dt, "$lte": end_dt},
                "deleted": {"$ne": True},
            }
        },
        {
            "$group": {
                "_id": None,
                "received": {"$sum": 1},
                "replied": {"$sum": {"$cond": [{"$ne": ["$replied_at", None]}, 1, 0]}},
                "high_priority": {"$sum": {"$cond": [{"$eq": ["$priority", "high"]}, 1, 0]}},
            }
        },
    ]
    email_res = await db["emails"].aggregate(email_pipeline).to_list(1)
    received = email_res[0]["received"] if email_res else 0
    replied = email_res[0]["replied"] if email_res else 0
    high_priority = email_res[0]["high_priority"] if email_res else 0

    # 2. Category & Intent breakdowns
    breakdowns = {}
    for field in ["category", "priority", "sentiment", "intent"]:
        pipeline = [
            {"$match": {"user_id": user_id, "received_at": {"$gte": start_dt, "$lte": end_dt}}},
            {"$group": {"_id": f"${field}", "count": {"$sum": 1}}},
        ]
        docs = await db["emails"].aggregate(pipeline).to_list(20)
        breakdowns[f"{field}_counts"] = {d["_id"]: d["count"] for d in docs if d["_id"]}

    # 3. Tasks & Meetings counts
    tasks_count = await db["tasks"].count_documents({
        "user_id": user_id,
        "created_at": {"$gte": start_dt, "$lte": end_dt},
    })
    meetings_count = await db["meetings"].count_documents({
        "user_id": user_id,
        "created_at": {"$gte": start_dt, "$lte": end_dt},
    })
    ai_replies_count = await db["reply_drafts"].count_documents({
        "user_id": user_id,
        "created_at": {"$gte": start_dt, "$lte": end_dt},
    })

    # 4. Time saved computation (minutes)
    time_saved_breakdown = {
        "email_categorization": received * 0.5,
        "ai_reply_generated": ai_replies_count * 3.0,
        "meeting_detected": meetings_count * 2.0,
        "task_extracted": tasks_count * 1.5,
        "email_summarized": received * 1.0,
    }
    total_time_saved = sum(time_saved_breakdown.values())

    from bson import ObjectId  # noqa: PLC0415
    snapshot = AnalyticsSnapshotModel(
        user_id=ObjectId(user_id) if isinstance(user_id, str) else user_id,
        snapshot_date=target_date,
        total_emails=received,
        emails_received=received,
        emails_replied=replied,
        high_priority_emails=high_priority,
        category_counts=breakdowns.get("category_counts", {}),
        priority_counts=breakdowns.get("priority_counts", {}),
        sentiment_counts=breakdowns.get("sentiment_counts", {}),
        intent_counts=breakdowns.get("intent_counts", {}),
        meetings_detected=meetings_count,
        tasks_extracted=tasks_count,
        ai_replies_generated=ai_replies_count,
        ai_time_saved_minutes=round(total_time_saved, 1),
        ai_time_saved_breakdown=time_saved_breakdown,
        created_at=datetime.now(timezone.utc),
    )

    repo = AnalyticsSnapshotRepository()
    saved = await repo.upsert_daily_snapshot(snapshot)
    logger.info("Generated analytics snapshot for user=%s date=%s", user_id, target_date)
    return saved


async def generate_daily_brief(user_id: str) -> str:
    """
    Generates a personalized daily briefing summary using Gemini.
    """
    db = get_database()
    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    today_end = today_start + timedelta(days=1)

    high_priority_emails = await db["emails"].find(
        {"user_id": user_id, "priority": "high", "is_read": False},
        limit=5,
    ).to_list(5)

    upcoming_meetings = await db["meetings"].find(
        {"user_id": user_id, "start_time": {"$gte": today_start, "$lte": today_end}},
        limit=5,
    ).to_list(5)

    pending_tasks = await db["tasks"].find(
        {"user_id": user_id, "status": "pending"},
        limit=5,
    ).to_list(5)

    context = (
        f"Unread High Priority Emails:\n"
        + "\n".join(f"- {e.get('subject', 'No Subject')} (From: {e.get('sender_email', '')})" for e in high_priority_emails)
        + "\n\nToday's Meetings:\n"
        + "\n".join(f"- {m.get('title', '')} at {m.get('start_time')}" for m in upcoming_meetings)
        + "\n\nPending Tasks:\n"
        + "\n".join(f"- {t.get('title', '')} (Due: {t.get('due_date', 'None')})" for t in pending_tasks)
    )

    client = get_gemini_client()
    try:
        brief = await client.generate_text(
            prompt=f"Prepare my daily briefing from the following data:\n\n{context}",
            system_prompt=DAILY_BRIEF_SYSTEM_PROMPT,
            temperature=0.3,
        )
        return brief
    except Exception as exc:
        logger.warning("Failed to generate daily brief via Gemini: %s", exc)
        return "Good morning! Here is your daily summary: check your inbox for urgent tasks."

