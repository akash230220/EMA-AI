# backend/app/schemas/settings_schema.py
from typing import Optional

from app.schemas.auth_schema import UserResponse
from app.schemas.common_schema import CamelModel


# ---------------------------------------------------------------------------
# Requests
# ---------------------------------------------------------------------------

class ProfileUpdateRequest(CamelModel):
    name: Optional[str] = None
    timezone: Optional[str] = None


class NotificationPreferencesUpdateRequest(CamelModel):
    high_priority_email: Optional[bool] = None
    meeting_detected: Optional[bool] = None
    task_detected: Optional[bool] = None
    daily_brief: Optional[bool] = None
    automation_fired: Optional[bool] = None
    weekly_digest: Optional[bool] = None


class AiPreferencesUpdateRequest(CamelModel):
    default_reply_tone: Optional[str] = None
    summary_length: Optional[str] = None
    auto_process_new_emails: Optional[bool] = None
    auto_sync_confirmed_meetings: Optional[bool] = None


# ---------------------------------------------------------------------------
# Responses
# ---------------------------------------------------------------------------

class IntegrationStatusResponse(CamelModel):
    connected: bool
    email: Optional[str] = None
    last_synced_at_label: Optional[str] = None


class NotificationPreferencesResponse(CamelModel):
    high_priority_email: bool
    meeting_detected: bool
    task_detected: bool
    daily_brief: bool
    automation_fired: bool
    weekly_digest: bool


class AiPreferencesResponse(CamelModel):
    default_reply_tone: str
    summary_length: str
    auto_process_new_emails: bool
    auto_sync_confirmed_meetings: bool


class SessionResponse(CamelModel):
    id: str
    device_label: str
    device_type: str
    location: Optional[str] = None
    last_active_label: str
    is_current: bool


class SettingsResponse(CamelModel):
    profile: UserResponse
    gmail_status: IntegrationStatusResponse
    calendar_status: IntegrationStatusResponse
    notification_preferences: NotificationPreferencesResponse
    ai_preferences: AiPreferencesResponse
    sessions: list[SessionResponse]