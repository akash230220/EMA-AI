"""RAG (Retrieval-Augmented Generation) package."""

from app.ai.rag.chunking.chunker import chunk_email_content, recursive_text_chunker
from app.ai.rag.embeddings.embedder import get_embedding, get_embeddings_batch
from app.ai.rag.vectorstore.chroma_client import (
    clear_user_index,
    delete_email_from_index,
    index_email,
    semantic_search_emails,
)

__all__ = [
    "recursive_text_chunker",
    "chunk_email_content",
    "get_embedding",
    "get_embeddings_batch",
    "index_email",
    "semantic_search_emails",
    "delete_email_from_index",
    "clear_user_index",
]

