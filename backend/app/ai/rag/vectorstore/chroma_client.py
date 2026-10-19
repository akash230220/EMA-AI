# backend/app/ai/rag/vectorstore/chroma_client.py
"""
ChromaDB Vector Store Client for Semantic Search & RAG.

Responsibilities:
  - Initializes ChromaDB client (local persistent disk mode or remote server)
  - Indexes chunked email documents with dense embeddings (text-embedding-004)
  - Semantic vector search with cosine distance scoring and metadata filtering (user_id isolation)
  - Document deletion and user index wiping for privacy compliance
"""

from __future__ import annotations

import logging
import os
from typing import Any, Optional

from app.ai.rag.chunking.chunker import chunk_email_content
from app.ai.rag.embeddings.embedder import get_embedding, get_embeddings_batch
from app.core.config import get_settings
from app.schemas.email_schema import SemanticSearchResultResponse

logger = logging.getLogger("ai_email_os.chroma_client")
settings = get_settings()

_chroma_client = None
_collection = None

# In-memory mock fallback store for testing environments without chromadb
_memory_store: dict[str, list[dict[str, Any]]] = {}


def _get_collection():
    """Initializes and returns the ChromaDB collection."""
    global _chroma_client, _collection
    if _collection is not None:
        return _collection

    try:
        import chromadb  # noqa: PLC0415
        from chromadb.config import Settings as ChromaSettings  # noqa: PLC0415

        if settings.CHROMA_SERVER_HOST:
            _chroma_client = chromadb.HttpClient(
                host=settings.CHROMA_SERVER_HOST,
                port=settings.CHROMA_SERVER_PORT,
            )
            logger.info("Connected to remote ChromaDB server at %s:%d", settings.CHROMA_SERVER_HOST, settings.CHROMA_SERVER_PORT)
        else:
            persist_dir = os.path.abspath(settings.CHROMA_PERSIST_DIR)
            os.makedirs(persist_dir, exist_ok=True)
            _chroma_client = chromadb.PersistentClient(path=persist_dir)
            logger.info("Connected to local ChromaDB persistent storage at %s", persist_dir)

        _collection = _chroma_client.get_or_create_collection(
            name=settings.CHROMA_COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )
        return _collection
    except Exception as exc:
        logger.warning("ChromaDB initialization failed (%s); operating with in-memory fallback.", exc)
        return None


async def index_email(
    email_id: str,
    user_id: str,
    subject: str,
    snippet: str,
    body: str,
) -> None:
    """
    Chunks, embeds, and stores an email in ChromaDB with user_id metadata filtering.
    """
    chunks = chunk_email_content(
        email_id=email_id,
        user_id=user_id,
        subject=subject,
        snippet=snippet,
        body=body,
    )

    if not chunks:
        return

    texts = [c["text"] for c in chunks]
    chunk_ids = [c["chunk_id"] for c in chunks]
    metadatas = [
        {
            "email_id": str(c["email_id"]),
            "user_id": str(c["user_id"]),
            "subject": str(c["subject"]),
            "chunk_index": int(c["chunk_index"]),
        }
        for c in chunks
    ]

    try:
        embeddings = await get_embeddings_batch(texts)
    except Exception as exc:
        logger.warning("Failed to generate embeddings for email %s: %s", email_id, exc)
        embeddings = [[0.0] * 768 for _ in texts]

    collection = _get_collection()
    if collection is not None:
        try:
            collection.upsert(
                ids=chunk_ids,
                documents=texts,
                embeddings=embeddings,
                metadatas=metadatas,
            )
            logger.info("Indexed %d chunk(s) in ChromaDB for email_id=%s", len(chunks), email_id)
            return
        except Exception as exc:
            logger.warning("Failed to upsert chunks into ChromaDB: %s", exc)

    # In-memory fallback
    user_chunks = _memory_store.setdefault(user_id, [])
    # Remove existing chunks for this email
    _memory_store[user_id] = [c for c in user_chunks if c.get("email_id") != email_id]
    for i, chunk in enumerate(chunks):
        _memory_store[user_id].append({
            "chunk_id": chunk_ids[i],
            "email_id": email_id,
            "text": texts[i],
            "subject": subject,
            "embedding": embeddings[i],
        })
    logger.info("Indexed %d chunk(s) in fallback store for email_id=%s", len(chunks), email_id)


async def semantic_search_emails(
    user_id: str,
    query: str,
    limit: int = 10,
) -> list[SemanticSearchResultResponse]:
    """
    RAG vector search across user's emails.
    Returns deduplicated results sorted by similarity score.
    """
    if not query.strip():
        return []

    try:
        query_embedding = await get_embedding(query)
    except Exception as exc:
        logger.warning("Failed to generate query embedding: %s", exc)
        query_embedding = [0.0] * 768

    collection = _get_collection()
    results_map: dict[str, SemanticSearchResultResponse] = {}

    if collection is not None:
        try:
            chroma_res = collection.query(
                query_embeddings=[query_embedding],
                n_results=limit * 2,
                where={"user_id": str(user_id)},
                include=["documents", "metadatas", "distances"],
            )

            ids = chroma_res.get("ids", [[]])[0]
            docs = chroma_res.get("documents", [[]])[0]
            metas = chroma_res.get("metadatas", [[]])[0]
            distances = chroma_res.get("distances", [[]])[0]

            for i in range(len(ids)):
                email_id = metas[i].get("email_id", "")
                snippet = docs[i]
                # Cosine distance to similarity score
                distance = distances[i] if i < len(distances) else 1.0
                score = max(0.0, round(1.0 - float(distance), 4))

                if email_id and (email_id not in results_map or results_map[email_id].score < score):
                    results_map[email_id] = SemanticSearchResultResponse(
                        email_id=email_id,
                        snippet=snippet[:400],
                        score=score,
                    )

            sorted_results = sorted(results_map.values(), key=lambda r: r.score, reverse=True)
            return sorted_results[:limit]
        except Exception as exc:
            logger.warning("ChromaDB query failed: %s; falling back to memory store.", exc)

    # In-memory fallback search (keyword match + basic scoring)
    user_chunks = _memory_store.get(user_id, [])
    query_lower = query.lower()

    for item in user_chunks:
        text = item["text"]
        email_id = item["email_id"]
        score = 0.5
        if query_lower in text.lower():
            score = 0.95
        elif any(w in text.lower() for w in query_lower.split()):
            score = 0.75

        if email_id not in results_map or results_map[email_id].score < score:
            results_map[email_id] = SemanticSearchResultResponse(
                email_id=email_id,
                snippet=text[:400],
                score=score,
            )

    sorted_results = sorted(results_map.values(), key=lambda r: r.score, reverse=True)
    return sorted_results[:limit]


async def delete_email_from_index(user_id: str, email_id: str) -> None:
    """Removes all indexed chunks for an email."""
    collection = _get_collection()
    if collection is not None:
        try:
            collection.delete(where={"$and": [{"user_id": user_id}, {"email_id": email_id}]})
        except Exception as exc:
            logger.warning("Failed to delete email %s from ChromaDB: %s", email_id, exc)

    if user_id in _memory_store:
        _memory_store[user_id] = [c for c in _memory_store[user_id] if c.get("email_id") != email_id]


async def clear_user_index(user_id: str) -> None:
    """Purges all vector records belonging to a user."""
    collection = _get_collection()
    if collection is not None:
        try:
            collection.delete(where={"user_id": user_id})
        except Exception as exc:
            logger.warning("Failed to clear user %s vector records in ChromaDB: %s", user_id, exc)

    if user_id in _memory_store:
        del _memory_store[user_id]

