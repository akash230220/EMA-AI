"""MongoDB Database package."""

from app.db.indexes import ensure_indexes
from app.db.mongo_client import (
    close_mongo_connection,
    connect_to_mongo,
    get_client,
    get_database,
    ping_mongo,
)

__all__ = [
    "get_client",
    "get_database",
    "connect_to_mongo",
    "close_mongo_connection",
    "ping_mongo",
    "ensure_indexes",
]
