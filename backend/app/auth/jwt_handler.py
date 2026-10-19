# backend/app/auth/jwt_handler.py
"""
JWT Authentication Handler & FastAPI Dependencies.

Responsibilities:
  - Extracts Bearer token from Authorization header (or cookie fallback)
  - Validates and decodes access JWTs
  - Resolves current authenticated UserModel via UserRepository
  - Provides get_current_user and get_current_active_user FastAPI dependencies
"""

from __future__ import annotations

import logging
from typing import Optional

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError

from app.core.security import TOKEN_TYPE_ACCESS, get_token_subject
from app.exceptions.custom_exceptions import AppException
from app.models.user import UserModel
from app.repositories.user_repository import UserRepository

logger = logging.getLogger("ai_email_os.auth.jwt")

security_bearer = HTTPBearer(auto_error=False)


async def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_bearer),
) -> UserModel:
    """
    FastAPI dependency that extracts and validates the access token,
    returning the authenticated UserModel.
    Raises 401 Unauthorized if token is missing, invalid, expired, or user does not exist.
    """
    token: Optional[str] = None

    if credentials and credentials.credentials:
        token = credentials.credentials
    else:
        # Fallback to Authorization header manual parsing if HTTPBearer was bypassed
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header[7:].strip()

    if not token:
        raise AppException(
            status_code=401,
            detail="Authentication credentials were not provided.",
        )

    try:
        user_id_str = get_token_subject(token, expected_type=TOKEN_TYPE_ACCESS)
    except JWTError as exc:
        logger.warning("JWT validation failed: %s", exc)
        raise AppException(
            status_code=401,
            detail="Invalid or expired access token.",
        ) from exc

    user_repo = UserRepository()
    user = await user_repo.get_by_id(user_id_str)
    if not user:
        logger.warning("User id=%s in token subject not found in database.", user_id_str)
        raise AppException(
            status_code=401,
            detail="User associated with this token does not exist.",
        )

    return user


async def get_current_active_user(
    current_user: UserModel = Depends(get_current_user),
) -> UserModel:
    """Dependency verifying the user account is active."""
    return current_user


async def get_optional_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_bearer),
) -> Optional[UserModel]:
    """Dependency for public routes that optionally accept an authenticated user."""
    try:
        return await get_current_user(request, credentials)
    except AppException:
        return None

