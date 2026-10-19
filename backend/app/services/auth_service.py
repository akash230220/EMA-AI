# backend/app/services/auth_service.py
"""
Authentication service — Google OAuth 2.0 flow, session management.

Responsibilities:
  - Build the Google consent-screen URL (used by GET /auth/google/login)
  - Exchange an authorization code for Google tokens, upsert the user
    document in MongoDB, and issue our own access + refresh JWTs
    (used by POST /auth/google/callback)
  - Refresh an expired access token from a refresh token stored in the
    httpOnly cookie (used by POST /auth/refresh)
  - Revoke a refresh-token session (used by POST /auth/logout)

All raw OAuth HTTP calls are delegated to
  integrations/google_oauth/oauth_client.py
All raw Mongo I/O is delegated to
  repositories/user_repository.py (UserRepository, SessionRepository)
"""

from __future__ import annotations

import hashlib
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple

from jose import JWTError

from app.core.config import get_settings
from app.core.security import (
    TOKEN_TYPE_REFRESH,
    create_access_token,
    create_refresh_token,
    get_token_subject,
)
from app.exceptions.custom_exceptions import AppException
from app.integrations.google_oauth.oauth_client import (
    build_authorization_url,
    exchange_authorization_code,
    get_google_user_info,
)
from app.models.user import GoogleOAuthTokens, SessionModel, UserModel
from app.repositories.user_repository import SessionRepository, UserRepository
from app.schemas.auth_schema import UserResponse

settings = get_settings()
logger = logging.getLogger("ai_email_os.auth_service")


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _hash_token(raw_token: str) -> str:
    """SHA-256 hash stored in sessions collection — raw token is never persisted."""
    return hashlib.sha256(raw_token.encode()).hexdigest()


def _user_to_response(user: UserModel) -> UserResponse:
    return UserResponse(
        id=str(user.id),
        name=user.name,
        email=user.email,
        avatar_url=user.avatar_url,
        timezone=user.timezone,
        created_at=user.created_at,
    )


async def _issue_session(user: UserModel) -> Tuple[str, str]:
    """
    Create and persist a new refresh-token session, then return
    (access_token, refresh_token) as raw JWTs.
    The caller (endpoint) sets the refresh token as an httpOnly cookie.
    """
    user_id_str = str(user.id)
    access_token = create_access_token(subject=user_id_str)
    refresh_token = create_refresh_token(subject=user_id_str)

    session = SessionModel(
        user_id=user.id,
        refresh_token_hash=_hash_token(refresh_token),
        expires_at=datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
    )
    session_repo = SessionRepository()
    await session_repo.insert_one(session)

    logger.info("Session created for user_id=%s", user_id_str)
    return access_token, refresh_token


# ---------------------------------------------------------------------------
# Public API consumed by endpoints/auth.py
# ---------------------------------------------------------------------------

def build_google_auth_url() -> str:
    """
    Constructs the Google OAuth 2.0 authorization URL for the consent
    screen redirect. Includes offline access (for refresh_token) and
    forces account selection so users can switch accounts.
    """
    return build_authorization_url(
        scopes=settings.GOOGLE_OAUTH_SCOPES,
        redirect_uri=settings.GOOGLE_OAUTH_REDIRECT_URI,
    )


async def exchange_code_for_session(
    code: str,
) -> Tuple[str, str, UserResponse]:
    """
    Full Google OAuth callback flow:
      1. Exchange auth code -> Google access/refresh tokens
      2. Fetch Google user profile (sub, email, name, avatar)
      3. Upsert user document in MongoDB
      4. Store OAuth tokens on user document
      5. Issue our own access + refresh JWT pair
      6. Persist session (refresh token hash)

    Returns (access_token, refresh_token, user_response).
    Raises AppException(401) on OAuth failure.
    """
    try:
        google_tokens = await exchange_authorization_code(
            code=code,
            redirect_uri=settings.GOOGLE_OAUTH_REDIRECT_URI,
        )
    except Exception as exc:
        logger.warning("Google OAuth code exchange failed: %s", exc)
        raise AppException(status_code=401, detail="Google OAuth code exchange failed.") from exc

    try:
        google_user = await get_google_user_info(google_tokens["access_token"])
    except Exception as exc:
        logger.warning("Failed to fetch Google user info: %s", exc)
        raise AppException(status_code=401, detail="Could not retrieve Google user profile.") from exc

    user_repo = UserRepository()
    existing = await user_repo.get_by_google_sub(google_user["sub"])

    expires_at = datetime.now(timezone.utc) + timedelta(
        seconds=google_tokens.get("expires_in", 3600)
    )

    # Preserve existing refresh_token if Google does not re-issue one
    # (Google only issues a new refresh_token on first auth or after revocation)
    existing_refresh = (
        existing.oauth_tokens.refresh_token
        if existing and existing.oauth_tokens
        else ""
    )
    oauth_tokens = GoogleOAuthTokens(
        access_token=google_tokens["access_token"],
        refresh_token=google_tokens.get("refresh_token") or existing_refresh,
        expires_at=expires_at,
        scopes=google_tokens.get("scope", "").split(),
        gmail_connected=True,
        calendar_connected=True,
    )

    now = datetime.now(timezone.utc)
    if existing:
        user = existing
        user.name = google_user.get("name", existing.name)
        user.avatar_url = google_user.get("picture", existing.avatar_url)
        user.oauth_tokens = oauth_tokens
        user.updated_at = now
    else:
        user = UserModel(
            google_sub=google_user["sub"],
            email=google_user["email"],
            name=google_user.get("name", ""),
            avatar_url=google_user.get("picture"),
            oauth_tokens=oauth_tokens,
            created_at=now,
            updated_at=now,
        )

    user = await user_repo.upsert_by_google_sub(user)
    logger.info("User upserted: email=%s id=%s", user.email, user.id)

    access_token, refresh_token = await _issue_session(user)
    return access_token, refresh_token, _user_to_response(user)


async def refresh_access_token(
    refresh_token: Optional[str],
) -> Tuple[str, UserResponse]:
    """
    Validates a refresh token (from httpOnly cookie), looks up the
    corresponding session, and issues a new short-lived access token.

    Raises AppException(401) on invalid/expired/revoked tokens.
    """
    if not refresh_token:
        raise AppException(status_code=401, detail="Refresh token missing.")

    try:
        user_id_str = get_token_subject(refresh_token, expected_type=TOKEN_TYPE_REFRESH)
    except JWTError as exc:
        raise AppException(status_code=401, detail="Invalid or expired refresh token.") from exc

    token_hash = _hash_token(refresh_token)
    session_repo = SessionRepository()
    session = await session_repo.find_one(
        {"refresh_token_hash": token_hash, "revoked": False}
    )
    if not session:
        raise AppException(status_code=401, detail="Session not found or has been revoked.")

    user_repo = UserRepository()
    user = await user_repo.get_by_id(user_id_str)
    if not user:
        raise AppException(status_code=401, detail="User not found.")

    # Touch last_active_at so session list on SettingsPage stays fresh
    await session_repo.update_one(
        {"_id": session.id},
        {"$set": {"last_active_at": datetime.now(timezone.utc)}},
    )

    new_access_token = create_access_token(subject=user_id_str)
    logger.debug("Access token refreshed for user_id=%s", user_id_str)
    return new_access_token, _user_to_response(user)


async def revoke_session(refresh_token: str) -> None:
    """
    Marks the session identified by the refresh-token hash as revoked.
    Called on logout so the stored cookie cannot be reused.
    """
    token_hash = _hash_token(refresh_token)
    session_repo = SessionRepository()
    session = await session_repo.find_one({"refresh_token_hash": token_hash})
    if session:
        await session_repo.update_one(
            {"_id": session.id},
            {"$set": {"revoked": True}},
        )
        logger.info("Session revoked: session_id=%s", session.id)


async def dev_login(
    email: str = "alex.mercer@company.com",
    name: str = "Alex Mercer",
) -> Tuple[str, str, UserResponse]:
    """
    Creates or retrieves a developer/demo user and issues session tokens.
    Available in development/testing mode to allow seamless local testing
    without external Google OAuth redirect dependencies.
    """
    user_repo = UserRepository()
    google_sub = f"dev_{email}"
    existing = await user_repo.get_by_google_sub(google_sub)

    now = datetime.now(timezone.utc)
    if existing:
        user = existing
    else:
        user = UserModel(
            google_sub=google_sub,
            email=email,
            name=name,
            avatar_url="https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=150&auto=format&fit=crop&q=80",
            oauth_tokens=GoogleOAuthTokens(
                access_token="dev_mock_access_token",
                refresh_token="dev_mock_refresh_token",
                expires_at=now + timedelta(days=365),
                scopes=settings.GOOGLE_OAUTH_SCOPES,
                gmail_connected=True,
                calendar_connected=True,
            ),
            created_at=now,
            updated_at=now,
        )
        user = await user_repo.upsert_by_google_sub(user)

    access_token, refresh_token = await _issue_session(user)
    return access_token, refresh_token, _user_to_response(user)

