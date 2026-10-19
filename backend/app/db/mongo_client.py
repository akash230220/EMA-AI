# backend/app/db/mongo_client.py
"""
MongoDB (Motor) Async Client Configuration & Connection Lifecycle.

Responsibilities:
  - Initializes the Motor async connection pool with production settings (pool sizes, timeouts)
  - Provides get_client() and get_database() accessors
  - Manages lifespan connection establishment, ping verification, and graceful shutdown
"""

from __future__ import annotations

import logging
from typing import Optional

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError

from app.core.config import get_settings

logger = logging.getLogger("ai_email_os.db")
settings = get_settings()

_client: Optional[AsyncIOMotorClient] = None


def get_client() -> AsyncIOMotorClient:
    """
    Returns the singleton AsyncIOMotorClient instance.
    Configures connection pooling and timeouts from application settings.
    """
    global _client
    if _client is None:
        logger.info("Initializing AsyncIOMotorClient pool to %s", settings.MONGODB_DB_NAME)
        _client = AsyncIOMotorClient(
            settings.MONGODB_URI,
            maxPoolSize=50,
            minPoolSize=10,
            serverSelectionTimeoutMS=5000,
            connectTimeoutMS=5000,
            socketTimeoutMS=10000,
            retryWrites=True,
            uuidRepresentation="standard",
        )
    return _client


def get_database() -> AsyncIOMotorDatabase:
    """Returns the configured AsyncIOMotorDatabase instance."""
    return get_client()[settings.MONGODB_DB_NAME]


async def connect_to_mongo() -> None:
    """
    Verifies connectivity to MongoDB on application startup.
    Raises ConnectionFailure if the database cannot be reached.
    """
    client = get_client()
    try:
        # Run admin ping command to verify active connection
        await client.admin.command("ping")
        logger.info("Successfully connected to MongoDB Atlas database '%s'", settings.MONGODB_DB_NAME)
    except (ConnectionFailure, ServerSelectionTimeoutError) as exc:
        logger.error("Failed to connect to MongoDB: %s", exc)
        raise ConnectionFailure(f"Could not connect to MongoDB at {settings.MONGODB_URI}: {exc}") from exc


async def close_mongo_connection() -> None:
    """Gracefully closes all connection pools on application shutdown."""
    global _client
    if _client is not None:
        logger.info("Closing MongoDB connection pool...")
        _client.close()
        _client = None
        logger.info("MongoDB connection closed.")


async def ping_mongo() -> bool:
    """
    Performs a lightweight ping check.
    Used by /api/health endpoint to report system readiness.
    """
    try:
        client = get_client()
        await client.admin.command("ping")
        return True
    except Exception as exc:
        logger.warning("MongoDB health check ping failed: %s", exc)
        return False
