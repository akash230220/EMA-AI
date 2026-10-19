# backend/app/db/indexes.py
"""
MongoDB Index Specifications.

Ensures all high-performance, compound, unique, and text search indexes exist
across all collections on application startup (main.py lifespan).
"""

from __future__ import annotations

import logging
from pymongo import ASCENDING, DESCENDING, TEXT

from app.db.mongo_client import get_database

logger = logging.getLogger("ai_email_os.indexes")


async def ensure_indexes() -> None:
    """
    Creates compound, unique, and query-optimized indexes across all collections.
    Safe to execute multiple times (idempotent via create_index).
    """
    db = get_database()
    logger.info("Verifying and ensuring MongoDB collection indexes...")

    # 1. Users collection
    await db.users.create_index("google_sub", unique=True, name="idx_users_google_sub_unique")
    await db.users.create_index("email", unique=True, name="idx_users_email_unique")

    # 2. Sessions collection
    await db.sessions.create_index("refresh_token_hash", unique=True, name="idx_sessions_token_hash")
    await db.sessions.create_index([("user_id", ASCENDING), ("revoked", ASCENDING)], name="idx_sessions_user_revoked")
    await db.sessions.create_index("expires_at", name="idx_sessions_expires_at")

    # 3. Emails collection
    # Deduplication & retrieval by Gmail IDs
    await db.emails.create_index(
        [("user_id", ASCENDING), ("gmail_message_id", ASCENDING)],
        unique=True,
        name="idx_emails_user_gmail_msg_id_unique",
    )
    await db.emails.create_index(
        [("user_id", ASCENDING), ("gmail_thread_id", ASCENDING)],
        name="idx_emails_user_gmail_thread_id",
    )

    # Inbox filters and sorting
    await db.emails.create_index([("user_id", ASCENDING), ("received_at", DESCENDING)], name="idx_emails_user_received_at")
    await db.emails.create_index([("user_id", ASCENDING), ("is_read", ASCENDING), ("received_at", DESCENDING)], name="idx_emails_user_is_read")
    await db.emails.create_index([("user_id", ASCENDING), ("archived", ASCENDING), ("received_at", DESCENDING)], name="idx_emails_user_archived")
    await db.emails.create_index([("user_id", ASCENDING), ("category", ASCENDING), ("received_at", DESCENDING)], name="idx_emails_user_category")
    await db.emails.create_index([("user_id", ASCENDING), ("priority", ASCENDING), ("received_at", DESCENDING)], name="idx_emails_user_priority")
    await db.emails.create_index([("user_id", ASCENDING), ("intent", ASCENDING), ("received_at", DESCENDING)], name="idx_emails_user_intent")
    await db.emails.create_index([("user_id", ASCENDING), ("pending_reply", ASCENDING)], name="idx_emails_user_pending_reply")
    await db.emails.create_index([("user_id", ASCENDING), ("deleted", ASCENDING)], name="idx_emails_user_deleted")

    # Full-text search fallback index
    await db.emails.create_index(
        [("subject", TEXT), ("snippet", TEXT), ("sender_email", TEXT)],
        name="idx_emails_text_search",
    )

    # 4. Tasks collection
    await db.tasks.create_index(
        [("user_id", ASCENDING), ("status", ASCENDING), ("due_date", ASCENDING)],
        name="idx_tasks_user_status_due_date",
    )
    await db.tasks.create_index([("user_id", ASCENDING), ("source_email_id", ASCENDING)], name="idx_tasks_user_email")
    await db.tasks.create_index([("user_id", ASCENDING), ("created_at", DESCENDING)], name="idx_tasks_user_created")

    # 5. Meetings collection
    await db.meetings.create_index([("user_id", ASCENDING), ("start_time", ASCENDING)], name="idx_meetings_user_start_time")
    await db.meetings.create_index([("user_id", ASCENDING), ("status", ASCENDING)], name="idx_meetings_user_status")
    await db.meetings.create_index([("user_id", ASCENDING), ("calendar_event_id", ASCENDING)], name="idx_meetings_user_cal_id")
    await db.meetings.create_index([("user_id", ASCENDING), ("source_email_id", ASCENDING)], name="idx_meetings_user_email")

    # 6. Automation Rules & Logs
    await db.automation_rules.create_index(
        [("user_id", ASCENDING), ("enabled", ASCENDING), ("priority", ASCENDING)],
        name="idx_automation_user_enabled_priority",
    )
    await db.rule_execution_logs.create_index(
        [("user_id", ASCENDING), ("rule_id", ASCENDING), ("executed_at", DESCENDING)],
        name="idx_rule_logs_user_rule_executed",
    )
    await db.rule_execution_logs.create_index(
        [("user_id", ASCENDING), ("email_id", ASCENDING)],
        name="idx_rule_logs_user_email",
    )

    # 7. Reply Drafts collection
    await db.reply_drafts.create_index([("user_id", ASCENDING), ("email_id", ASCENDING)], name="idx_reply_drafts_user_email")

    # 8. Analytics Snapshots
    await db.analytics_snapshots.create_index(
        [("user_id", ASCENDING), ("snapshot_date", DESCENDING)],
        unique=True,
        name="idx_analytics_user_date_unique",
    )

    # 9. Copilot Conversations
    await db.copilot_conversations.create_index(
        [("user_id", ASCENDING), ("last_message_at", DESCENDING)],
        name="idx_copilot_user_last_message",
    )

    logger.info("All MongoDB collection indexes verified and built successfully.")
