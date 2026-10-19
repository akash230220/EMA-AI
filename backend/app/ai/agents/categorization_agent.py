# backend/app/ai/agents/categorization_agent.py
"""
Categorization Agent.

Classifies incoming emails into core business categories:
work, finance, personal, newsletters, promotions, social.
"""

from __future__ import annotations

import logging
from typing import Any

from app.ai.gemini.gemini_client import get_gemini_client
from app.ai.prompts.prompt_library import CATEGORIZATION_SYSTEM_PROMPT

logger = logging.getLogger("ai_email_os.categorization_agent")

VALID_CATEGORIES = {"work", "finance", "personal", "newsletters", "promotions", "social"}


async def categorize_email(subject: str, transcript: str) -> dict[str, Any]:
    """
    Invokes Gemini to categorize email based on subject and thread transcript.
    Returns: {"category": str, "confidence": float, "reasoning": str}
    """
    client = get_gemini_client()
    prompt = f"Subject: {subject}\n\nEmail Content:\n{transcript[:3000]}"

    try:
        result = await client.generate_json(
            prompt=prompt,
            system_prompt=CATEGORIZATION_SYSTEM_PROMPT,
            temperature=0.1,
        )
        category = result.get("category", "work").lower().strip()
        if category not in VALID_CATEGORIES:
            category = "work"

        return {
            "category": category,
            "confidence": float(result.get("confidence", 0.9)),
            "reasoning": result.get("reasoning", ""),
        }
    except Exception as exc:
        logger.warning("Categorization Agent failed; defaulting to 'work': %s", exc)
        return {
            "category": "work",
            "confidence": 0.5,
            "reasoning": "Fallback classification",
        }

