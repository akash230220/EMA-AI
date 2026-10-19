"""Authentication & Authorization package."""

from app.auth.jwt_handler import (
    get_current_active_user,
    get_current_user,
    get_optional_current_user,
)
from app.auth.oauth_handler import (
    REFRESH_COOKIE_NAME,
    clear_refresh_cookie,
    generate_oauth_state,
    set_refresh_cookie,
    verify_oauth_state,
)
from app.auth.rbac import Role, require_admin, require_role

__all__ = [
    "get_current_user",
    "get_current_active_user",
    "get_optional_current_user",
    "generate_oauth_state",
    "verify_oauth_state",
    "set_refresh_cookie",
    "clear_refresh_cookie",
    "REFRESH_COOKIE_NAME",
    "Role",
    "require_role",
    "require_admin",
]

