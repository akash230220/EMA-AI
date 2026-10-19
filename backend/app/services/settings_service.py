# backend/app/services/settings_service.py
"""
User Settings service — profile, preferences, integrations, and session security.

Responsibilities:
  - get_user_settings: aggregates profile, integration status, notification & AI preferences, and active sessions
  - update_profile: updates user display name and timezone
  - update_notification_preferences: updates notification flags
  - update_ai_preferences: updates tone, summary length, auto-processing settings
  - disconnect_google_integration: revokes Google OAuth tokens and marks integrations disconnected
  - revoke_session / revoke_all_sessions: terminates user sessions
  - clear_ai_data: resets all AI derived tags, summaries, and embeddings across user's emails
  - delete_account: permanently deletes the user account and cascading data
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Optional

from app.db.mongo_client import get_database
from app.exceptions.custom_exceptions import AppException
from app.integrations.google_oauth.oauth_client import revoke_google_token
from app.models.user import AiPreferences, NotificationPreferences, UserModel
from app.repositories.user_repository import SessionRepository, UserRepository
from app.schemas.auth_schema import UserResponse
from app.schemas.settings_schema import (
    AiPreferencesResponse,
    AiPreferencesUpdateRequest,
    IntegrationStatusResponse,
    NotificationPreferencesResponse,
    NotificationPreferencesUpdateRequest,
    SessionResponse,
    SettingsResponse,
)
from app.utils.datetime_utils import format_datetime_label

logger = logging.getLogger("ai_email_os.settings_service")


async def get_user_settings(user_id: str) -> SettingsResponse:
    """Returns the full settings aggregate for the user."""
    user_repo = UserRepository()
    user = await user_repo.get_by_id(user_id)
    if not user:
        raise AppException(status_code=404, detail="User not found.")

    gmail_connected = bool(user.oauth_tokens and user.oauth_tokens.gmail_connected)
    calendar_connected = bool(user.oauth_tokens and user.oauth_tokens.calendar_connected)

    gmail_synced_label = (
        format_datetime_label(user.oauth_tokens.last_gmail_synced_at)
        if user.oauth_tokens and user.oauth_tokens.last_gmail_synced_at
        else None
    )
    calendar_synced_label = (
        format_datetime_label(user.oauth_tokens.last_calendar_synced_at)
        if user.oauth_tokens and user.oauth_tokens.last_calendar_synced_at
        else None
    )

    session_repo = SessionRepository()
    sessions = await session_repo.get_active_sessions_for_user(user_id)
    session_responses = [
        SessionResponse(
            id=str(s.id),
            device_label=s.device_label,
            device_type=s.device_type,
            location=s.location,
            last_active_label=format_datetime_label(s.last_active_at),
            is_current=False,
        )
        for s in sessions
    ]

    return SettingsResponse(
        profile=UserResponse(
            id=str(user.id),
            name=user.name,
            email=user.email,
            avatar_url=user.avatar_url,
            timezone=user.timezone,
            created_at=user.created_at,
        ),
        gmail_status=IntegrationStatusResponse(
            connected=gmail_connected,
            email=user.email if gmail_connected else None,
            last_synced_at_label=gmail_synced_label,
        ),
        calendar_status=IntegrationStatusResponse(
            connected=calendar_connected,
            email=user.email if calendar_connected else None,
            last_synced_at_label=calendar_synced_label,
        ),
        notification_preferences=NotificationPreferencesResponse(
            high_priority_email=user.notification_preferences.high_priority_email,
            meeting_detected=user.notification_preferences.meeting_detected,
            task_detected=user.notification_preferences.task_detected,
            daily_brief=user.notification_preferences.daily_brief,
            automation_fired=user.notification_preferences.automation_fired,
            weekly_digest=user.notification_preferences.weekly_digest,
        ),
        ai_preferences=AiPreferencesResponse(
            default_reply_tone=user.ai_preferences.default_reply_tone,
            summary_length=user.ai_preferences.summary_length,
            auto_process_new_emails=user.ai_preferences.auto_process_new_emails,
            auto_sync_confirmed_meetings=user.ai_preferences.auto_sync_confirmed_meetings,
        ),
        sessions=session_responses,
    )


async def update_profile(
    user_id: str,
    name: Optional[str] = None,
    timezone_str: Optional[str] = None,
) -> UserResponse:
    user_repo = UserRepository()
    updates: dict = {"updated_at": datetime.now(timezone.utc)}
    if name is not None:
        updates["name"] = name
    if timezone_str is not None:
        updates["timezone"] = timezone_str

    updated = await user_repo.update_one({"_id": user_id}, {"$set": updates})
    if not updated:
        raise AppException(status_code=404, detail="User not found.")
    return UserResponse(
        id=str(updated.id),
        name=updated.name,
        email=updated.email,
        avatar_url=updated.avatar_url,
        timezone=updated.timezone,
        created_at=updated.created_at,
    )


async def update_notification_preferences(
    user_id: str, preferences: NotificationPreferencesUpdateRequest
) -> NotificationPreferencesResponse:
    user_repo = UserRepository()
    user = await user_repo.get_by_id(user_id)
    if not user:
        raise AppException(status_code=404, detail="User not found.")

    current = user.notification_preferences.model_dump()
    for key, val in preferences.model_dump(exclude_none=True).items():
        current[key] = val

    updated = await user_repo.update_one(
        {"_id": user_id},
        {
            "$set": {
                "notification_preferences": current,
                "updated_at": datetime.now(timezone.utc),
            }
        },
    )
    if not updated:
        raise AppException(status_code=404, detail="User not found.")
    return NotificationPreferencesResponse(**updated.notification_preferences.model_dump())


async def update_ai_preferences(
    user_id: str, preferences: AiPreferencesUpdateRequest
) -> AiPreferencesResponse:
    user_repo = UserRepository()
    user = await user_repo.get_by_id(user_id)
    if not user:
        raise AppException(status_code=404, detail="User not found.")

    current = user.ai_preferences.model_dump()
    for key, val in preferences.model_dump(exclude_none=True).items():
        current[key] = val

    updated = await user_repo.update_one(
        {"_id": user_id},
        {
            "$set": {
                "ai_preferences": current,
                "updated_at": datetime.now(timezone.utc),
            }
        },
    )
    if not updated:
        raise AppException(status_code=404, detail="User not found.")
    return AiPreferencesResponse(**updated.ai_preferences.model_dump())


async def disconnect_google_integration(user_id: str) -> None:
    user_repo = UserRepository()
    user = await user_repo.get_by_id(user_id)
    if not user or not user.oauth_tokens:
        return

    # Attempt to revoke token at Google
    if user.oauth_tokens.refresh_token:
        try:
            await revoke_google_token(user.oauth_tokens.refresh_token)
        except Exception as exc:
            logger.warning("Revoke token error: %s", exc)

    await user_repo.update_one(
        {"_id": user_id},
        {
            "$set": {
                "oauth_tokens.gmail_connected": False,
                "oauth_tokens.calendar_connected": False,
                "oauth_tokens.access_token": "",
                "oauth_tokens.refresh_token": "",
                "updated_at": datetime.now(timezone.utc),
            }
        },
    )
    logger.info("Google integration disconnected for user_id=%s", user_id)


async def revoke_session(user_id: str, session_id: str) -> None:
    session_repo = SessionRepository()
    await session_repo.update_one(
        {"_id": session_id, "user_id": user_id},
        {"$set": {"revoked": True}},
    )


async def revoke_all_sessions(user_id: str) -> None:
    session_repo = SessionRepository()
    await session_repo.collection.update_many(
        session_repo._normalize_filter({"user_id": user_id}),
        {"$set": {"revoked": True}},
    )


async def clear_ai_data(user_id: str) -> None:
    """Clears all AI analysis fields and summaries so emails can be re-analyzed."""
    db = get_database()
    await db["emails"].update_many(
        {"user_id": user_id},
        {
            "$set": {
                "category": None,
                "priority": None,
                "intent": None,
                "sentiment": None,
                "ai_summary": None,
                "ai_key_points": [],
                "ai_processed_at": None,
                "embedding_indexed": False,
                "updated_at": datetime.now(timezone.utc),
            }
        },
    )
    logger.info("Cleared AI data for user_id=%s", user_id)


async def delete_account(user_id: str) -> None:
    """Permanently purges all user data across all collections."""
    db = get_database()
    collections = [
        "users",
        "sessions",
        "emails",
        "reply_drafts",
        "tasks",
        "meetings",
        "automation_rules",
        "rule_execution_logs",
        "analytics_snapshots",
        "copilot_conversations",
    ]
    for col in collections:
        if col == "users":
            await db[col].delete_one({"_id": user_id})
        else:
            await db[col].delete_many({"user_id": user_id})
    logger.info("Account and all associated collections deleted for user_id=%s", user_id)

