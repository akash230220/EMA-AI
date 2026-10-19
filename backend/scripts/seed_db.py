# backend/scripts/seed_db.py
"""
Seeds the database with realistic sample data for local development
and demos — a test user, a batch of emails spanning every
category/priority/intent/sentiment combination, tasks, meetings, an
automation rule, and a Copilot conversation.

Usage:
    python -m scripts.seed_db
    python -m scripts.seed_db --wipe        # clears existing data first
    python -m scripts.seed_db --user-email you@example.com

Safe to run against a local/dev MongoDB only — refuses to run when
ENVIRONMENT=production as a guardrail against accidentally seeding a
real database.
"""

import argparse
import asyncio
import logging
import random
import sys
from datetime import datetime, timedelta, timezone

from bson import ObjectId  # type: ignore[reportMissingImports]
from motor.motor_asyncio import AsyncIOMotorClient  # type: ignore[reportMissingImports]

from app.core.config import get_settings
from app.models.user import UserModel, NotificationPreferences, AiPreferences
from app.models.email import EmailModel, ThreadMessage
from app.models.task import TaskModel
from app.models.meeting import MeetingModel
from app.models.automation_rule import AutomationRuleModel, RuleCondition, RuleAction
from app.models.copilot import CopilotConversationModel, CopilotMessageModel

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger("seed_db")

settings = get_settings()

CATEGORIES = ["work", "finance", "personal", "newsletters", "promotions", "social"]
PRIORITIES = ["high", "medium", "low"]
INTENTS = ["meeting_request", "task", "fyi", "follow_up", "urgent_action", "question"]
SENTIMENTS = ["positive", "neutral", "negative"]

SAMPLE_SENDERS = [
    ("Priya Sharma", "priya.sharma@acmecorp.com"),
    ("James Whitfield", "james.whitfield@vendorco.com"),
    ("Notion", "team@mail.notion.so"),
    ("Ava Chen", "ava.chen@acmecorp.com"),
    ("LinkedIn", "notifications@linkedin.com"),
    ("Marcus Reid", "marcus.reid@clientfirm.com"),
    ("Google Cloud", "billing@cloud.google.com"),
    ("Sofia Martins", "sofia.martins@acmecorp.com"),
]

SAMPLE_SUBJECTS = [
    "Q3 Budget Review — action needed by Friday",
    "Re: Contract renewal terms",
    "Your weekly digest is here",
    "Meeting request: Product roadmap sync",
    "Invoice #4521 — payment confirmation",
    "Quick question about the API migration",
    "FYI: Office closed Monday for maintenance",
    "Follow up: onboarding checklist",
    "Urgent: production deploy blocked",
    "Team lunch this Friday?",
]


def _rand_choice(items):
    return random.choice(items)


async def seed(db, user_email: str, num_emails: int) -> None:
    now = datetime.now(timezone.utc)

    # ------------------------------------------------------------------
    # User
    # ------------------------------------------------------------------
    user = UserModel(
        google_sub=f"seed-google-sub-{ObjectId()}",
        email=user_email,
        name="Ak (Seed User)",
        timezone="Asia/Kolkata",
        notification_preferences=NotificationPreferences(),
        ai_preferences=AiPreferences(),
    )
    await db.users.insert_one(user.to_mongo())
    user_id = user.id
    logger.info("Created seed user: %s (%s)", user.email, user_id)

    # ------------------------------------------------------------------
    # Emails
    # ------------------------------------------------------------------
    email_ids = []
    for i in range(num_emails):
        sender_name, sender_email = _rand_choice(SAMPLE_SENDERS)
        subject = _rand_choice(SAMPLE_SUBJECTS)
        received_at = now - timedelta(hours=random.randint(1, 24 * 14))
        category = _rand_choice(CATEGORIES)
        priority = _rand_choice(PRIORITIES)
        intent = _rand_choice(INTENTS)
        sentiment = _rand_choice(SENTIMENTS)

        thread_message = ThreadMessage(
            id=f"gmail-msg-{i}-{ObjectId()}",
            sender_name=sender_name,
            sender_email=sender_email,
            recipients=[user_email],
            snippet=f"{subject} — this is a seeded sample message body for local development.",
            body_text=(
                f"Hi,\n\n{subject}\n\nThis is placeholder seed content used for local development "
                f"and UI testing. It does not reflect a real conversation.\n\nBest,\n{sender_name}"
            ),
            sent_at=received_at,
        )

        email = EmailModel(
            user_id=user_id,
            gmail_thread_id=f"gmail-thread-{i}-{ObjectId()}",
            gmail_message_id=thread_message.id,
            subject=subject,
            sender_name=sender_name,
            sender_email=sender_email,
            snippet=thread_message.snippet,
            thread=[thread_message],
            category=category,
            priority=priority,
            intent=intent,
            sentiment=sentiment,
            ai_summary=f"AI summary: {subject.split('—')[0].strip()}.",
            ai_key_points=[f"Key point about {category}", f"Priority flagged as {priority}"],
            ai_processed_at=received_at,
            ai_pipeline_version="seed-v1",
            is_read=random.random() > 0.4,
            is_starred=random.random() > 0.85,
            pending_reply=intent in ("question", "urgent_action") and random.random() > 0.5,
            has_attachment=random.random() > 0.8,
            received_at=received_at,
        )
        result = await db.emails.insert_one(email.to_mongo())
        email_ids.append(result.inserted_id)

    logger.info("Inserted %d seed emails.", len(email_ids))

    # ------------------------------------------------------------------
    # Tasks (mix of AI-extracted, linked to a seeded email, and manual)
    # ------------------------------------------------------------------
    task_titles = [
        "Send Q3 report to finance team",
        "Follow up with vendor on contract terms",
        "Review API migration plan",
        "Prepare onboarding materials for new hire",
        "Confirm Friday's budget meeting agenda",
    ]
    for i, title in enumerate(task_titles):
        is_ai = i % 2 == 0
        task = TaskModel(
            user_id=user_id,
            title=title,
            description="Seeded sample task for local development." if i % 3 == 0 else None,
            due_date=(now + timedelta(days=random.randint(-2, 10))).date(),
            priority=_rand_choice(PRIORITIES),
            status=_rand_choice(["pending", "in_progress", "completed"]),
            source="ai_extracted" if is_ai else "manual",
            source_email_id=_rand_choice(email_ids) if is_ai and email_ids else None,
        )
        await db.tasks.insert_one(task.to_mongo())
    logger.info("Inserted %d seed tasks.", len(task_titles))

    # ------------------------------------------------------------------
    # Meetings
    # ------------------------------------------------------------------
    meeting_titles = [
        ("Q3 Budget Review", "detected"),
        ("Product roadmap sync", "confirmed"),
        ("1:1 with Marcus", "synced"),
        ("Vendor contract discussion", "declined"),
    ]
    for i, (title, status) in enumerate(meeting_titles):
        start = now + timedelta(days=random.randint(0, 10), hours=random.randint(9, 16))
        meeting = MeetingModel(
            user_id=user_id,
            title=title,
            description="Seeded sample meeting for local development.",
            location="Google Meet" if i % 2 == 0 else "Conference Room A",
            attendees=[sender_email for _, sender_email in random.sample(SAMPLE_SENDERS, k=2)],
            start_time=start,
            end_time=start + timedelta(minutes=30),
            status=status,
            source="ai_detected" if i % 2 == 0 else "manual",
            source_email_id=_rand_choice(email_ids) if i % 2 == 0 and email_ids else None,
            calendar_event_id=f"gcal-evt-{ObjectId()}" if status == "synced" else None,
        )
        await db.meetings.insert_one(meeting.to_mongo())
    logger.info("Inserted %d seed meetings.", len(meeting_titles))

    # ------------------------------------------------------------------
    # Automation rule
    # ------------------------------------------------------------------
    rule = AutomationRuleModel(
        user_id=user_id,
        name="Auto-archive newsletters",
        description="Automatically archives low-priority newsletter emails.",
        conditions=[
            RuleCondition(field="category", operator="equals", value="newsletters"),
            RuleCondition(field="priority", operator="equals", value="low"),
        ],
        condition_logic="AND",
        actions=[RuleAction(type="archive")],
        enabled=True,
        priority=0,
    )
    await db.automation_rules.insert_one(rule.to_mongo())
    logger.info("Inserted 1 seed automation rule.")

    # ------------------------------------------------------------------
    # Copilot conversation
    # ------------------------------------------------------------------
    conversation = CopilotConversationModel(
        user_id=user_id,
        title="What's pending this week?",
        messages=[
            CopilotMessageModel(role="user", content="What's pending this week?"),
            CopilotMessageModel(
                role="assistant",
                content=(
                    "You have 3 high-priority emails awaiting a reply and 2 meetings scheduled "
                    "in the next 7 days. Want me to draft replies for the pending emails?"
                ),
                tool_calls=[],
                sources=[],
            ),
        ],
        last_message_at=now,
    )
    await db.copilot_conversations.insert_one(conversation.to_mongo())
    logger.info("Inserted 1 seed Copilot conversation.")

    logger.info("Seed complete. User id: %s | Email: %s", user_id, user_email)


async def wipe(db) -> None:
    collections = [
        "users", "sessions", "emails", "reply_drafts", "tasks", "meetings",
        "automation_rules", "rule_execution_logs", "copilot_conversations",
        "analytics_snapshots",
    ]
    for name in collections:
        result = await db[name].delete_many({})
        logger.info("Wiped %s: %d documents removed.", name, result.deleted_count)


async def main():
    parser = argparse.ArgumentParser(description="Seed AI Email OS database with sample data.")
    parser.add_argument("--wipe", action="store_true", help="Delete existing data before seeding.")
    parser.add_argument("--user-email", default="dev@example.com", help="Email for the seeded user.")
    parser.add_argument("--num-emails", type=int, default=40, help="Number of sample emails to generate.")
    args = parser.parse_args()

    if settings.is_production:
        logger.error("Refusing to run seed_db.py against ENVIRONMENT=production. Aborting.")
        sys.exit(1)

    client = AsyncIOMotorClient(settings.MONGODB_URI)
    db = client[settings.MONGODB_DB_NAME]

    try:
        if args.wipe:
            logger.info("Wiping existing data...")
            await wipe(db)

        await seed(db, user_email=args.user_email, num_emails=args.num_emails)
    finally:
        client.close()


if __name__ == "__main__":
    asyncio.run(main())