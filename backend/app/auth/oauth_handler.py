# backend/app/auth/oauth_handler.py
"""
OAuth State & Secure Cookie Utilities.

Responsibilities:
  - Generates & verifies signed CSRF state tokens for Google OAuth redirects
  - Sets and deletes httpOnly secure refresh cookies on FastAPI responses
"""

from __future__ import annotations

import hmac
import logging
import secrets
from typing import Optional

from fastapi import Response

from app.core.config import get_settings

logger = logging.getLogger("ai_email_os.auth.oauth")
settings = get_settings()

REFRESH_COOKIE_NAME = "refresh_token"


def generate_oauth_state() -> str:
    """Generates a cryptographically random state parameter for OAuth CSRF protection."""
    random_bytes = secrets.token_hex(16)
    signature = hmac.new(
        settings.JWT_SECRET_KEY.encode(),
        random_bytes.encode(),
        digestmod="sha256",
    ).hexdigest()
    return f"{random_bytes}.{signature}"


def verify_oauth_state(state: str) -> bool:
    """Verifies HMAC signature of an incoming OAuth state string."""
    if not state or "." not in state:
        return False
    random_bytes, signature = state.split(".", 1)
    expected_signature = hmac.new(
        settings.JWT_SECRET_KEY.encode(),
        random_bytes.encode(),
        digestmod="sha256",
    ).hexdigest()
    return hmac.compare_digest(signature, expected_signature)


def set_refresh_cookie(
    response: Response,
    refresh_token: str,
    max_age_days: Optional[int] = None,
) -> None:
    """
    Sets the refresh token as an httpOnly, Secure, SameSite=Lax cookie.
    Cookie path is restricted to /api/v1/auth to prevent transmission on every API request.
    """
    days = max_age_days or settings.REFRESH_TOKEN_EXPIRE_DAYS
    max_age_seconds = days * 24 * 60 * 60

    response.set_cookie(
        key=REFRESH_COOKIE_NAME,
        value=refresh_token,
        httponly=True,
        secure=settings.is_production,
        samesite="lax",
        max_age=max_age_seconds,
        path="/api/v1/auth",
    )
    logger.debug("Set secure httpOnly refresh cookie (max_age=%ds, secure=%s)", max_age_seconds, settings.is_production)


def clear_refresh_cookie(response: Response) -> None:
    """Clears the refresh token cookie upon logout."""
    response.delete_cookie(
        key=REFRESH_COOKIE_NAME,
        path="/api/v1/auth",
        httponly=True,
        secure=settings.is_production,
        samesite="lax",
    )
    logger.debug("Cleared refresh cookie.")

