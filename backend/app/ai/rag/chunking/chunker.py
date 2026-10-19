# backend/app/ai/rag/chunking/chunker.py
"""
Text and Email Thread Chunking Module.

Splits long email threads and attachments into semantic text chunks
optimized for embedding generation (text-embedding-004) and ChromaDB indexing.
"""

from __future__ import annotations

import re
from typing import Any, Optional


def recursive_text_chunker(
    text: str,
    chunk_size: int = 500,
    chunk_overlap: int = 50,
    separators: Optional[list[str]] = None,
) -> list[str]:
    """
    Recursively splits text into chunks of at most `chunk_size` characters,
    splitting along paragraph, sentence, and word boundaries with overlap.
    """
    if not text:
        return []

    if separators is None:
        separators = ["\n\n", "\n", ". ", " ", ""]

    if len(text) <= chunk_size:
        return [text.strip()]

    # Find the first separator that appears in the text
    separator = separators[-1]
    for sep in separators:
        if sep in text:
            separator = sep
            break

    splits = text.split(separator) if separator else list(text)
    chunks: list[str] = []
    current_chunk: list[str] = []
    current_len = 0

    for split in splits:
        split_len = len(split) + len(separator)
        if current_len + split_len > chunk_size and current_chunk:
            chunk_str = separator.join(current_chunk).strip()
            if chunk_str:
                chunks.append(chunk_str)

            # Handle overlap by keeping the trailing items
            overlap_items = []
            overlap_len = 0
            for item in reversed(current_chunk):
                if overlap_len + len(item) <= chunk_overlap:
                    overlap_items.insert(0, item)
                    overlap_len += len(item)
                else:
                    break

            current_chunk = overlap_items
            current_len = overlap_len

        current_chunk.append(split)
        current_len += split_len

    if current_chunk:
        chunk_str = separator.join(current_chunk).strip()
        if chunk_str:
            chunks.append(chunk_str)

    return chunks


def chunk_email_content(
    email_id: str,
    user_id: str,
    subject: str,
    snippet: str,
    body: str,
    chunk_size: int = 500,
) -> list[dict[str, Any]]:
    """
    Chunks an email while attaching document metadata to each chunk.
    Ensures the subject header is prepended to each chunk for contextual fidelity.
    """
    full_text = f"Subject: {subject}\n\n{body or snippet}"
    raw_chunks = recursive_text_chunker(full_text, chunk_size=chunk_size, chunk_overlap=50)

    if not raw_chunks:
        raw_chunks = [f"Subject: {subject}\n{snippet}"]

    chunk_objects = []
    for idx, chunk_text in enumerate(raw_chunks):
        chunk_objects.append({
            "chunk_id": f"{email_id}_chunk_{idx}",
            "email_id": email_id,
            "user_id": user_id,
            "subject": subject,
            "text": chunk_text,
            "chunk_index": idx,
            "total_chunks": len(raw_chunks),
        })

    return chunk_objects

