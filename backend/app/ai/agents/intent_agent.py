# backend/app/ai/agents/intent_agent.py
"""
Intent Agent.

Detects primary intent: meeting_request, task, fyi, follow_up, urgent_action, question.
"""

from __future__ import annotations

import logging
from typing import Any

from app.ai.gemini.gemini_client import get_gemini_client
from app.ai.prompts.prompt_library import INTENT_SYSTEM_PROMPT

logger = logging.getLogger("ai_email_os.intent_agent")

VALID_INTENTS = {
    "meeting_request",
    "task",
    "fyi",
    "follow_up",
    "urgent_action",
    "question",
}


async def detect_intent(subject: str, transcript: str) -> dict[str, Any]:
    """
    Invokes Gemini to detect the primary intent and whether action is required.
    """
    client = get_gemini_client()
    prompt = f"Subject: {subject}\n\nEmail Content:\n{transcript[:3000]}"

    try:
        result = await client.generate_json(
            prompt=prompt,
            system_prompt=INTENT_SYSTEM_PROMPT,
            temperature=0.1,
        )
        intent = result.get("intent", "fyi").lower().strip()
        if intent not in VALID_INTENTS:
            intent = "fyi"

        return {
            "intent": intent,
            "confidence": float(result.get("confidence", 0.9)),
            "action_required": bool(result.get("action_required", False)),
        }
    except Exception as exc:
        logger.warning("Intent Agent failed; defaulting to 'fyi': %s", exc)
        return {
            "intent": "fyi",
            "confidence": 0.5,
            "action_required": False,
        }

