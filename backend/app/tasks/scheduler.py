# backend/app/tasks/scheduler.py
"""
Background Scheduler & Asynchronous Recurring Tasks.

Responsibilities:
  - Periodic Gmail inbox synchronization for all active connected users
    (cadence: settings.INBOX_SYNC_INTERVAL_MINUTES)
  - Nightly analytics rollups (aggregates yesterday's activity into AnalyticsSnapshotModel)
  - Morning executive daily briefing generation
    (cadence: settings.DAILY_BRIEF_HOUR_UTC)
  - Graceful startup and shutdown lifecycle management for FastAPI lifespan
"""

from __future__ import annotations

import asyncio
import logging
from datetime import date, datetime, timedelta, timezone
from typing import Optional

from app.core.config import get_settings
from app.db.mongo_client import get_database

logger = logging.getLogger("ai_email_os.scheduler")
settings = get_settings()

_scheduler = None
_background_tasks: list[asyncio.Task] = []
_is_running = False


# ---------------------------------------------------------------------------
# Background Job Handlers
# ---------------------------------------------------------------------------

async def run_inbox_sync_job() -> None:
    """
    Polls Gmail for all users who have an active Gmail connection.
    Runs every INBOX_SYNC_INTERVAL_MINUTES.
    """
    logger.info("Executing scheduled recurring inbox sync job...")
    db = get_database()

    try:
        # Find all users with active Gmail connection
        cursor = db["users"].find(
            {"oauth_tokens.gmail_connected": True},
            projection={"_id": 1, "email": 1},
        )
        users = await cursor.to_list(length=1000)
    except Exception as exc:
        logger.error("Failed to query connected users for inbox sync: %s", exc)
        return

    logger.info("Found %d user(s) eligible for scheduled Gmail sync.", len(users))

    from app.services.inbox_service import trigger_inbox_sync  # noqa: PLC0415

    for user_doc in users:
        user_id_str = str(user_doc["_id"])
        try:
            res = await trigger_inbox_sync(user_id=user_id_str, full_sync=False)
            if res.synced_count > 0:
                logger.info("Auto-synced %d email(s) for user %s", res.synced_count, user_doc.get("email"))
        except Exception as exc:
            logger.warning("Scheduled sync failed for user %s: %s", user_id_str, exc)


async def run_daily_briefing_job() -> None:
    """
    Aggregates daily analytics snapshots and generates executive daily briefings.
    Runs once daily at settings.DAILY_BRIEF_HOUR_UTC.
    """
    logger.info("Executing scheduled daily analytics rollup & briefing job...")
    db = get_database()
    yesterday = date.today() - timedelta(days=1)

    try:
        cursor = db["users"].find({}, projection={"_id": 1, "notification_preferences": 1})
        users = await cursor.to_list(length=1000)
    except Exception as exc:
        logger.error("Failed to query users for daily briefing job: %s", exc)
        return

    from app.ai.agents.analytics_agent import (  # noqa: PLC0415
        generate_daily_brief,
        generate_daily_snapshot,
    )

    for user_doc in users:
        user_id_str = str(user_doc["_id"])
        try:
            # 1. Roll up yesterday's analytics
            await generate_daily_snapshot(user_id=user_id_str, target_date=yesterday)

            # 2. Generate morning brief if user preferences allow
            prefs = user_doc.get("notification_preferences", {})
            if prefs.get("daily_brief", True):
                brief_text = await generate_daily_brief(user_id=user_id_str)
                logger.debug("Generated daily brief for user_id=%s (len=%d)", user_id_str, len(brief_text))
        except Exception as exc:
            logger.warning("Daily briefing rollup failed for user %s: %s", user_id_str, exc)


# ---------------------------------------------------------------------------
# Scheduler Loops & Fallback Worker
# ---------------------------------------------------------------------------

async def _periodic_inbox_sync_loop() -> None:
    """Async loop running inbox sync on interval."""
    interval_seconds = max(60, settings.INBOX_SYNC_INTERVAL_MINUTES * 60)
    logger.info("Started background inbox sync worker loop (interval=%ds).", interval_seconds)

    while _is_running:
        try:
            await run_inbox_sync_job()
        except asyncio.CancelledError:
            break
        except Exception as exc:
            logger.exception("Unexpected error in inbox sync loop: %s", exc)

        try:
            await asyncio.sleep(interval_seconds)
        except asyncio.CancelledError:
            break


async def _daily_briefing_loop() -> None:
    """Async loop running daily analytics rollup once every 24 hours."""
    logger.info("Started background daily briefing worker loop.")

    while _is_running:
        try:
            now = datetime.now(timezone.utc)
            # Compute target run time today at DAILY_BRIEF_HOUR_UTC
            target = now.replace(
                hour=settings.DAILY_BRIEF_HOUR_UTC,
                minute=0,
                second=0,
                microsecond=0,
            )
            if now >= target:
                target += timedelta(days=1)

            sleep_seconds = (target - now).total_seconds()
            logger.debug("Daily briefing scheduled to run in %.1f hours.", sleep_seconds / 3600.0)

            await asyncio.sleep(sleep_seconds)
            if _is_running:
                await run_daily_briefing_job()
        except asyncio.CancelledError:
            break
        except Exception as exc:
            logger.exception("Unexpected error in daily briefing loop: %s", exc)
            await asyncio.sleep(300)


# ---------------------------------------------------------------------------
# Lifespan Start & Shutdown
# ---------------------------------------------------------------------------

def start_scheduler() -> None:
    """
    Initializes and starts background tasks.
    Tries APScheduler first; falls back to native asyncio background tasks.
    """
    global _scheduler, _is_running, _background_tasks
    _is_running = True

    try:
        from apscheduler.schedulers.asyncio import AsyncIOScheduler  # noqa: PLC0415
        from apscheduler.triggers.cron import CronTrigger  # noqa: PLC0415
        from apscheduler.triggers.interval import IntervalTrigger  # noqa: PLC0415

        _scheduler = AsyncIOScheduler()

        # Job 1: Recurring inbox sync
        _scheduler.add_job(
            run_inbox_sync_job,
            trigger=IntervalTrigger(minutes=settings.INBOX_SYNC_INTERVAL_MINUTES),
            id="inbox_sync_job",
            name="Gmail Inbox Sync Poller",
            replace_existing=True,
        )

        # Job 2: Daily Briefing & Snapshot Rollup
        _scheduler.add_job(
            run_daily_briefing_job,
            trigger=CronTrigger(hour=settings.DAILY_BRIEF_HOUR_UTC, minute=0),
            id="daily_briefing_job",
            name="Daily Analytics & Briefing Generator",
            replace_existing=True,
        )

        _scheduler.start()
        logger.info("APScheduler started successfully with 2 recurring jobs.")
        return
    except ImportError:
        logger.info("APScheduler not installed; launching native asyncio background loops.")

    # Fallback to native asyncio loops
    loop = asyncio.get_event_loop()
    sync_task = loop.create_task(_periodic_inbox_sync_loop())
    brief_task = loop.create_task(_daily_briefing_loop())
    _background_tasks.extend([sync_task, brief_task])
    logger.info("Native asyncio background scheduler tasks launched.")


def shutdown_scheduler() -> None:
    """Stops all running background scheduler tasks gracefully."""
    global _scheduler, _is_running, _background_tasks
    _is_running = False

    if _scheduler is not None:
        try:
            _scheduler.shutdown(wait=False)
            logger.info("APScheduler shut down.")
        except Exception as exc:
            logger.warning("Error shutting down APScheduler: %s", exc)
        _scheduler = None

    for task in _background_tasks:
        if not task.done():
            task.cancel()
    _background_tasks.clear()
    logger.info("Background scheduler tasks cancelled and stopped.")

