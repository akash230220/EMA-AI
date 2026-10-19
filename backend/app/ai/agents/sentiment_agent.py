# backend/app/ai/agents/sentiment_agent.py
"""
Sentiment Agent.

Analyzes emotional tone and sentiment polarity (positive, neutral, negative).
"""

from __future__ import annotations

import logging
from typing import Any

from app.ai.gemini.gemini_client import get_gemini_client
from app.ai.prompts.prompt_library import SENTIMENT_SYSTEM_PROMPT

logger = logging.getLogger("ai_email_os.sentiment_agent")

VALID_SENTIMENTS = {"positive", "neutral", "negative"}


async def analyze_sentiment(subject: str, transcript: str) -> dict[str, Any]:
    """
    Invokes Gemini to determine email tone and sentiment.
    """
    client = get_gemini_client()
    prompt = f"Subject: {subject}\n\nEmail Content:\n{transcript[:3000]}"

    try:
        result = await client.generate_json(
            prompt=prompt,
            system_prompt=SENTIMENT_SYSTEM_PROMPT,
            temperature=0.1,
        )
        sentiment = result.get("sentiment", "neutral").lower().strip()
        if sentiment not in VALID_SENTIMENTS:
            sentiment = "neutral"

        return {
            "sentiment": sentiment,
            "score": float(result.get("score", 0.0)),
            "tone_keywords": result.get("tone_keywords", []),
        }
    except Exception as exc:
        logger.warning("Sentiment Agent failed; defaulting to 'neutral': %s", exc)
        return {
            "sentiment": "neutral",
            "score": 0.0,
            "tone_keywords": [],
        }

