# backend/scripts/clear_db.py
"""
Wipes every collection in the configured database. Standalone from
seed_db.py's --wipe flag so it can be run on its own (e.g. resetting
a dev environment without immediately re-seeding).

Usage:
    python -m scripts.clear_db            # prompts for confirmation
    python -m scripts.clear_db --yes      # skips confirmation (CI use)

Refuses to run when ENVIRONMENT=production, same guardrail as
seed_db.py — this script is destructive and has no undo.
"""

import argparse
import asyncio
import logging
import sys

from motor.motor_asyncio import AsyncIOMotorClient  # type: ignore[import-not-found]

from app.core.config import get_settings

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger("clear_db")

settings = get_settings()

COLLECTIONS = [
    "users", "sessions", "emails", "reply_drafts", "tasks", "meetings",
    "automation_rules", "rule_execution_logs", "copilot_conversations",
    "analytics_snapshots",
]


async def clear_all(db) -> None:
    for name in COLLECTIONS:
        result = await db[name].delete_many({})
        logger.info("Cleared %s: %d documents removed.", name, result.deleted_count)


async def main():
    parser = argparse.ArgumentParser(description="Delete all documents from every AI Email OS collection.")
    parser.add_argument("--yes", action="store_true", help="Skip the interactive confirmation prompt.")
    args = parser.parse_args()

    if settings.is_production:
        logger.error("Refusing to run clear_db.py against ENVIRONMENT=production. Aborting.")
        sys.exit(1)

    if not args.yes:
        confirm = input(
            f"This will permanently delete ALL data in database "
            f"'{settings.MONGODB_DB_NAME}' at {settings.MONGODB_URI}.\n"
            f"Type 'yes' to continue: "
        )
        if confirm.strip().lower() != "yes":
            logger.info("Aborted — no data was deleted.")
            return

    client = AsyncIOMotorClient(settings.MONGODB_URI)
    db = client[settings.MONGODB_DB_NAME]

    try:
        await clear_all(db)
        logger.info("Database cleared.")
    finally:
        client.close()


if __name__ == "__main__":
    asyncio.run(main())