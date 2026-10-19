# backend/app/ai/agents/priority_agent.py
"""
Priority Agent.

Assesses email urgency and importance (high, medium, low) using Gemini.
"""

from __future__ import annotations

import logging
from typing import Any

from app.ai.gemini.gemini_client import get_gemini_client
from app.ai.prompts.prompt_library import PRIORITY_SYSTEM_PROMPT

logger = logging.getLogger("ai_email_os.priority_agent")

VALID_PRIORITIES = {"high", "medium", "low"}


async def detect_priority(subject: str, transcript: str, category: str = "work", intent: str = "fyi") -> dict[str, Any]:
    """
    Invokes Gemini to evaluate the urgency level of an email.
    """
    client = get_gemini_client()
    prompt = (
        f"Subject: {subject}\n"
        f"Category: {category}\n"
        f"Intent: {intent}\n\n"
        f"Email Content:\n{transcript[:3000]}"
    )

    try:
        result = await client.generate_json(
            prompt=prompt,
            system_prompt=PRIORITY_SYSTEM_PROMPT,
            temperature=0.1,
        )
        priority = result.get("priority", "medium").lower().strip()
        if priority not in VALID_PRIORITIES:
            priority = "medium"

        return {
            "priority": priority,
            "score": int(result.get("score", 5)),
            "reasoning": result.get("reasoning", ""),
        }
    except Exception as exc:
        logger.warning("Priority Agent failed; defaulting to 'medium': %s", exc)
        return {
            "priority": "medium",
            "score": 5,
            "reasoning": "Fallback default priority",
        }

