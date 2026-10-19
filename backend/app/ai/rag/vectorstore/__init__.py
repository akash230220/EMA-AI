"""Vectorstore package."""

from app.ai.rag.vectorstore.chroma_client import (
    clear_user_index,
    delete_email_from_index,
    index_email,
    semantic_search_emails,
)

__all__ = [
    "index_email",
    "semantic_search_emails",
    "delete_email_from_index",
    "clear_user_index",
]

