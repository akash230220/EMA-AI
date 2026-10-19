# backend/app/ai/agents/task_agent.py
"""
Task Extraction Agent.

Scans email text for commitments, deliverables, and action items.
Extracts structured tasks and saves them as TaskModel documents linked to the email.
"""

from __future__ import annotations

import logging
from datetime import date, datetime, timezone
from typing import Any, Optional

from app.ai.gemini.gemini_client import get_gemini_client
from app.ai.prompts.prompt_library import TASK_EXTRACTION_SYSTEM_PROMPT
from app.models.email import DetectedTaskRef
from app.models.task import TaskModel
from app.repositories.task_repository import TaskRepository

logger = logging.getLogger("ai_email_os.task_agent")


def _parse_date(date_str: Optional[str]) -> Optional[date]:
    if not date_str:
        return None
    try:
        return datetime.fromisoformat(date_str.replace("Z", "+00:00")).date()
    except Exception:
        return None


async def extract_tasks(
    subject: str,
    transcript: str,
    user_id: str,
    email_id: str,
) -> list[DetectedTaskRef]:
    """
    Extracts tasks from email content and stores them in the tasks collection.
    Returns a list of DetectedTaskRef denormalized objects to attach to the EmailModel.
    """
    client = get_gemini_client()
    prompt = f"Subject: {subject}\n\nEmail Content:\n{transcript[:4000]}"

    try:
        result = await client.generate_json(
            prompt=prompt,
            system_prompt=TASK_EXTRACTION_SYSTEM_PROMPT,
            temperature=0.1,
        )
        extracted_list = result.get("tasks", [])
    except Exception as exc:
        logger.warning("Task Agent LLM call failed: %s", exc)
        return []

    if not extracted_list:
        return []

    task_repo = TaskRepository()
    detected_refs: list[DetectedTaskRef] = []
    now = datetime.now(timezone.utc)

    for item in extracted_list:
        title = item.get("title", "").strip()
        if not title:
            continue

        due_date = _parse_date(item.get("due_date"))
        priority = item.get("priority", "medium")

        from bson import ObjectId  # noqa: PLC0415
        task = TaskModel(
            user_id=ObjectId(user_id) if isinstance(user_id, str) else user_id,
            title=title,
            description=item.get("description"),
            due_date=due_date,
            priority=priority,
            status="pending",
            source="ai_extracted",
            source_email_id=ObjectId(email_id) if isinstance(email_id, str) else email_id,
            created_at=now,
            updated_at=now,
        )

        saved = await task_repo.insert_one(task)
        detected_refs.append(
            DetectedTaskRef(
                task_id=saved.id,
                title=saved.title,
                status=saved.status,
            )
        )

    logger.info("Task Agent extracted %d task(s) for email id=%s", len(detected_refs), email_id)
    return detected_refs

