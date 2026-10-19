# backend/scripts/create_indexes.py
"""
Standalone CLI wrapper around db/indexes.py's ensure_indexes() —
useful for provisioning indexes on a fresh database (e.g. right after
creating a new MongoDB Atlas cluster for staging/production) without
starting the full FastAPI app, which normally calls this
automatically via main.py's lifespan on every startup.

Usage:
    python -m scripts.create_indexes
"""

import asyncio
import logging

from app.db.mongo_client import connect_to_mongo, close_mongo_connection
from app.db.indexes import ensure_indexes

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger("create_indexes")


async def main():
    logger.info("Connecting to MongoDB...")
    await connect_to_mongo()

    logger.info("Ensuring indexes...")
    await ensure_indexes()
    logger.info("Indexes created/verified successfully.")

    await close_mongo_connection()


if __name__ == "__main__":
    asyncio.run(main())