# backend/app/ai/rag/embeddings/embedder.py
"""
RAG Embedding Generator.

Interfaces with Gemini's text-embedding-004 model to produce 768-dimensional dense vectors.
"""

from __future__ import annotations

import logging
from typing import Optional

from app.ai.gemini.gemini_client import get_gemini_client

logger = logging.getLogger("ai_email_os.embedder")


async def get_embedding(text: str, model: str = "text-embedding-004") -> list[float]:
    """Generates a dense vector embedding for a single text string."""
    client = get_gemini_client()
    return await client.embed_content(text, model=model)


async def get_embeddings_batch(texts: list[str], model: str = "text-embedding-004") -> list[list[float]]:
    """Generates embeddings for a batch of text strings."""
    if not texts:
        return []
    client = get_gemini_client()
    return await client.batch_embed_contents(texts, model=model)

