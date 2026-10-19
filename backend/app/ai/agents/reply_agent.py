# backend/app/ai/agents/reply_agent.py
"""
Reply Agent.

Generates professional, context-aware email replies across formal, friendly, and concise tones.
Integrates RAG retrieval for personalization based on user style and historical replies.
"""

from __future__ import annotations

import logging
from typing import Optional

from app.ai.gemini.gemini_client import get_gemini_client
from app.ai.prompts.prompt_library import REPLY_GENERATION_SYSTEM_PROMPT

logger = logging.getLogger("ai_email_os.reply_agent")


async def generate_reply(
    thread_text: str,
    tone: str = "friendly",
    instructions: Optional[str] = None,
    user_id: Optional[str] = None,
) -> str:
    """
    Generates a high quality draft reply.
    """
    client = get_gemini_client()

    # Retrieve optional past reply snippets for RAG context
    rag_context = ""
    if user_id:
        try:
            from app.ai.rag.vectorstore.chroma_client import semantic_search_emails  # noqa: PLC0415
            rag_results = await semantic_search_emails(
                user_id=user_id,
                query=thread_text[:200],
                limit=2,
            )
            if rag_results:
                rag_context = (
                    "\n\nReference Examples of Past Replies:\n"
                    + "\n".join(f"- {r.snippet[:200]}" for r in rag_results)
                )
        except Exception:
            pass  # RAG context is optional enhancement

    custom_instructions_block = (
        f"\n\nUser's Specific Instructions: {instructions}" if instructions else ""
    )

    prompt = (
        f"Desired Tone: {tone}\n"
        f"{custom_instructions_block}"
        f"{rag_context}\n\n"
        f"Email Thread:\n{thread_text[:3500]}\n\n"
        f"Write a {tone} reply:"
    )

    try:
        reply_body = await client.generate_text(
            prompt=prompt,
            system_prompt=REPLY_GENERATION_SYSTEM_PROMPT,
            temperature=0.4 if tone == "friendly" else 0.2,
        )
        return reply_body.strip()
    except Exception as exc:
        logger.exception("Reply Agent generation failed: %s", exc)
        return f"Thank you for your message. I have received your email regarding this matter and will get back to you shortly.\n\nBest regards,"

