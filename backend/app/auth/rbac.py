# backend/app/auth/rbac.py
"""
Role-Based Access Control (RBAC) Dependencies.

Defines system roles and FastAPI dependencies for route-level authorization.
"""

from __future__ import annotations

import logging
from enum import Enum
from typing import Callable

from fastapi import Depends

from app.auth.jwt_handler import get_current_user
from app.exceptions.custom_exceptions import AppException
from app.models.user import UserModel

logger = logging.getLogger("ai_email_os.auth.rbac")


class Role(str, Enum):
    USER = "user"
    ADMIN = "admin"


def require_role(required_role: Role | str) -> Callable:
    """
    Dependency factory that checks if the authenticated user possesses the required role.
    Raises 403 Forbidden if the user's role is insufficient.
    """
    role_str = required_role.value if isinstance(required_role, Role) else required_role

    async def role_checker(current_user: UserModel = Depends(get_current_user)) -> UserModel:
        if current_user.role != role_str and current_user.role != Role.ADMIN.value:
            logger.warning(
                "Access denied for user_id=%s (role=%s). Required: %s",
                current_user.id,
                current_user.role,
                role_str,
            )
            raise AppException(
                status_code=403,
                detail="You do not have permission to access this resource.",
            )
        return current_user

    return role_checker


# Pre-configured convenience dependency for admin-only endpoints
require_admin = require_role(Role.ADMIN)

