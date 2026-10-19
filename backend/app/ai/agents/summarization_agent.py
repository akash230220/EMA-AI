# backend/app/ai/agents/summarization_agent.py
"""
Summarization Agent.

Generates concise 1-2 sentence summaries and key bullet points for emails and threads.
"""

from __future__ import annotations

import logging
from typing import Any

from app.ai.gemini.gemini_client import get_gemini_client
from app.ai.prompts.prompt_library import SUMMARIZATION_SYSTEM_PROMPT
from app.models.email import EmailModel

logger = logging.getLogger("ai_email_os.summarization_agent")


async def summarize_email(subject: str, transcript: str) -> dict[str, Any]:
    """
    Generates summary and bullet points for the email.
    Returns: {"summary": str, "key_points": list[str]}
    """
    client = get_gemini_client()
    prompt = f"Subject: {subject}\n\nEmail Content:\n{transcript[:4000]}"

    try:
        result = await client.generate_json(
            prompt=prompt,
            system_prompt=SUMMARIZATION_SYSTEM_PROMPT,
            temperature=0.2,
        )
        summary = result.get("summary", "")
        key_points = result.get("key_points", [])

        if not summary:
            summary = transcript[:150].replace("\n", " ").strip() + "..."

        return {
            "summary": summary,
            "key_points": key_points if isinstance(key_points, list) else [],
        }
    except Exception as exc:
        logger.warning("Summarization Agent failed: %s", exc)
        return {
            "summary": transcript[:150].replace("\n", " ").strip() + "...",
            "key_points": [],
        }


async def generate_summary_for_email(email: EmailModel) -> str:
    """
    Convenience wrapper used by email_service.get_email_summary on-demand.
    """
    transcript = "\n\n".join(
        f"From: {msg.sender_email}\n{msg.body_text or msg.snippet}"
        for msg in email.thread
    ) or email.snippet

    res = await summarize_email(subject=email.subject, transcript=transcript)
    return res["summary"]

