# backend/app/ai/agents/reader_agent.py
"""
Reader Agent.

First agent in the LangGraph email processing pipeline.
Responsibilities:
  - Normalizes raw email text/HTML content
  - Strips email quotes, tracking pixels, and boilerplate disclaimers
  - Aggregates multi-message thread history into a chronological transcript
  - Computes message stats (word count, reading time)
"""

from __future__ import annotations

import logging
import re
from typing import Any

from app.models.email import EmailModel

logger = logging.getLogger("ai_email_os.reader_agent")


def clean_email_body(text: str) -> str:
    """Strips reply chains, disclaimers, and excessive whitespace."""
    if not text:
        return ""

    # Remove standard email quote lines (On ... wrote:, > quote)
    cleaned = re.sub(r"^>.*$", "", text, flags=re.MULTILINE)
    cleaned = re.sub(r"On .* at .* wrote:.*$", "", cleaned, flags=re.DOTALL | re.IGNORECASE)
    cleaned = re.sub(r"-{2,}\s*Original Message\s*-{2,}.*$", "", cleaned, flags=re.DOTALL | re.IGNORECASE)
    cleaned = re.sub(r"-{2,}\s*Forwarded Message\s*-{2,}.*$", "", cleaned, flags=re.DOTALL | re.IGNORECASE)

    # Normalize multiple newlines
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    return cleaned.strip()


async def read_email(email: EmailModel) -> dict[str, Any]:
    """
    Parses and pre-processes an EmailModel document into a clean structured payload.
    """
    messages = email.thread or []
    formatted_messages = []

    for msg in messages:
        raw_content = msg.body_text or msg.snippet or ""
        cleaned_content = clean_email_body(raw_content)
        formatted_messages.append({
            "sender_name": msg.sender_name,
            "sender_email": msg.sender_email,
            "sent_at": msg.sent_at.isoformat() if msg.sent_at else None,
            "body": cleaned_content,
        })

    # If thread was empty, use top-level fields
    if not formatted_messages:
        formatted_messages.append({
            "sender_name": email.sender_name,
            "sender_email": email.sender_email,
            "sent_at": email.received_at.isoformat() if email.received_at else None,
            "body": clean_email_body(email.snippet),
        })

    combined_transcript = "\n\n---\n\n".join(
        f"From: {m['sender_name'] or m['sender_email']} ({m['sender_email']})\n"
        f"Date: {m['sent_at']}\n\n"
        f"{m['body']}"
        for m in formatted_messages
    )

    words = len(combined_transcript.split())
    estimated_read_seconds = max(5, int(words / 3.5))

    logger.debug("Reader agent processed email id=%s (words=%d)", email.id, words)

    return {
        "email_id": str(email.id),
        "subject": email.subject,
        "sender_email": email.sender_email,
        "sender_name": email.sender_name,
        "thread_transcript": combined_transcript,
        "word_count": words,
        "estimated_read_seconds": estimated_read_seconds,
    }

