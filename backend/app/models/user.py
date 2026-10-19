# backend/app/models/user.py
"""
User document — the account record created/updated on Google OAuth
login. One document per authenticated user; Gmail/Calendar OAuth
tokens are stored here (encrypted at rest is a deployment-level
concern — see docs/deployment for KMS/field-level encryption notes).
"""

from datetime import datetime
from typing import Optional

from pydantic import EmailStr, Field

from app.models.base import MongoBaseModel, utcnow


class NotificationPreferences(MongoBaseModel.__base__):
    """Embedded sub-document — not a top-level collection."""

    model_config = {"populate_by_name": True}

    high_priority_email: bool = True
    meeting_detected: bool = True
    task_detected: bool = True
    daily_brief: bool = True
    automation_fired: bool = True
    weekly_digest: bool = False


class AiPreferences(MongoBaseModel.__base__):
    model_config = {"populate_by_name": True}

    default_reply_tone: str = "friendly"  # formal | friendly | concise
    summary_length: str = "medium"  # short | medium | detailed
    auto_process_new_emails: bool = True
    auto_sync_confirmed_meetings: bool = False


class GoogleOAuthTokens(MongoBaseModel.__base__):
    """
    Stored per-user OAuth grant. `access_token` is short-lived and
    refreshed on demand by integrations/google_oauth/oauth_client.py;
    `refresh_token` is long-lived and what actually matters for
    persistent Gmail/Calendar access.
    """

    model_config = {"populate_by_name": True}

    access_token: str
    refresh_token: str
    expires_at: datetime
    scopes: list[str] = Field(default_factory=list)
    gmail_connected: bool = True
    calendar_connected: bool = True
    last_gmail_synced_at: Optional[datetime] = None
    last_calendar_synced_at: Optional[datetime] = None


class UserModel(MongoBaseModel):
    """Collection: `users`"""

    google_sub: str = Field(..., description="Google's stable unique user identifier (the OAuth `sub` claim).")
    email: EmailStr
    name: str
    avatar_url: Optional[str] = None
    timezone: str = "UTC"

    oauth_tokens: Optional[GoogleOAuthTokens] = None
    notification_preferences: NotificationPreferences = Field(default_factory=NotificationPreferences)
    ai_preferences: AiPreferences = Field(default_factory=AiPreferences)

    role: str = "user"  # user | admin — see auth/rbac.py

    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)


class SessionModel(MongoBaseModel):
    """
    Collection: `sessions` — one document per refresh-token session,
    enabling per-device revocation (SecuritySettings.jsx's session
    list + revoke actions).
    """

    user_id: "PyObjectIdRef"  # see forward-ref note below
    refresh_token_hash: str = Field(..., description="SHA-256 hash of the refresh token, never the raw token.")
    device_label: str = "Unknown device"
    device_type: str = "desktop"  # desktop | mobile
    location: Optional[str] = None
    user_agent: Optional[str] = None
    ip_address: Optional[str] = None

    created_at: datetime = Field(default_factory=utcnow)
    last_active_at: datetime = Field(default_factory=utcnow)
    expires_at: datetime
    revoked: bool = False


# Deferred import to avoid a circular reference at module load time
from app.models.base import PyObjectId as PyObjectIdRef  # noqa: E402

SessionModel.model_rebuild()