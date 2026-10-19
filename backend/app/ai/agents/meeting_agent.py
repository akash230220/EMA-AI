# backend/app/ai/agents/meeting_agent.py
"""
Meeting Detection Agent.

Scans email text for meeting requests, invitations, and proposed calendar slots.
Extracts structured meetings and saves them as MeetingModel documents linked to the email.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

from app.ai.gemini.gemini_client import get_gemini_client
from app.ai.prompts.prompt_library import MEETING_DETECTION_SYSTEM_PROMPT
from app.models.email import DetectedMeetingRef
from app.models.meeting import MeetingModel
from app.repositories.meeting_repository import MeetingRepository

logger = logging.getLogger("ai_email_os.meeting_agent")


def _parse_datetime(dt_str: Optional[str]) -> Optional[datetime]:
    if not dt_str:
        return None
    try:
        dt = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except Exception:
        return None


async def detect_meetings(
    subject: str,
    transcript: str,
    user_id: str,
    email_id: str,
) -> list[DetectedMeetingRef]:
    """
    Detects meeting requests in the email and persists them into the meetings collection.
    Returns a list of DetectedMeetingRef objects to attach to the EmailModel.
    """
    client = get_gemini_client()
    prompt = f"Subject: {subject}\n\nEmail Content:\n{transcript[:4000]}"

    try:
        result = await client.generate_json(
            prompt=prompt,
            system_prompt=MEETING_DETECTION_SYSTEM_PROMPT,
            temperature=0.1,
        )
        extracted_meetings = result.get("meetings", [])
    except Exception as exc:
        logger.warning("Meeting Agent LLM call failed: %s", exc)
        return []

    if not extracted_meetings:
        return []

    meeting_repo = MeetingRepository()
    detected_refs: list[DetectedMeetingRef] = []
    now = datetime.now(timezone.utc)

    for item in extracted_meetings:
        title = item.get("title", "").strip() or f"Meeting: {subject[:40]}"
        start_time = _parse_datetime(item.get("start_time"))

        if not start_time:
            continue

        end_time = _parse_datetime(item.get("end_time"))
        if not end_time or end_time <= start_time:
            end_time = start_time + timedelta(minutes=30)

        from bson import ObjectId  # noqa: PLC0415
        meeting = MeetingModel(
            user_id=ObjectId(user_id) if isinstance(user_id, str) else user_id,
            title=title,
            description=item.get("description"),
            location=item.get("location"),
            attendees=item.get("attendees", []),
            start_time=start_time,
            end_time=end_time,
            status="detected",
            source="ai_detected",
            source_email_id=ObjectId(email_id) if isinstance(email_id, str) else email_id,
            created_at=now,
            updated_at=now,
        )

        saved = await meeting_repo.insert_one(meeting)
        detected_refs.append(
            DetectedMeetingRef(
                meeting_id=saved.id,
                title=saved.title,
                start_time=saved.start_time,
                status=saved.status,
            )
        )

    logger.info("Meeting Agent detected %d meeting(s) for email id=%s", len(detected_refs), email_id)
    return detected_refs

