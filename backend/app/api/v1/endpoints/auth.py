# backend/app/api/v1/endpoints/auth.py
"""
Auth endpoints — Google OAuth 2.0 login flow, session bootstrap,
token refresh, logout. Maps 1:1 to frontend/src/api/authApi.js.
"""

import hmac
from urllib.parse import urlencode

from fastapi import APIRouter, Depends, Query, Request, Response
from fastapi.responses import RedirectResponse

from app.schemas.auth_schema import UserResponse, TokenExchangeRequest, AccessTokenResponse
from app.services.auth_service import (
    build_google_auth_url,
    exchange_code_for_session,
    refresh_access_token,
    revoke_session,
    dev_login,
)
from app.exceptions.custom_exceptions import AppException
from app.auth.jwt_handler import get_current_user
from app.auth.oauth_handler import (
    generate_oauth_state,
    verify_oauth_state,
)
from app.core.config import get_settings

router = APIRouter()
settings = get_settings()

REFRESH_COOKIE_NAME = "refresh_token"
OAUTH_STATE_COOKIE_NAME = "oauth_state"
OAUTH_STATE_MAX_AGE_SECONDS = 600


def _clear_oauth_state_cookie(response: Response) -> None:
    response.delete_cookie(
        key=OAUTH_STATE_COOKIE_NAME,
        path="/api/v1/auth",
        httponly=True,
        secure=settings.is_production,
        samesite="lax",
    )


@router.get("/google/login")
async def google_login():
    """Starts a browser-bound Google OAuth flow with CSRF protection."""
    state = generate_oauth_state()
    auth_url = build_google_auth_url(state=state)
    response = RedirectResponse(url=auth_url)
    response.set_cookie(
        key=OAUTH_STATE_COOKIE_NAME,
        value=state,
        httponly=True,
        secure=settings.is_production,
        samesite="lax",
        max_age=OAUTH_STATE_MAX_AGE_SECONDS,
        path="/api/v1/auth",
    )
    return response


@router.get("/google/callback")
async def google_callback_redirect(
    request: Request,
    code: str | None = Query(None),
    state: str | None = Query(None),
    error: str | None = Query(None),
):
    """Validates OAuth state before forwarding the result to the frontend."""
    expected_state = request.cookies.get(OAUTH_STATE_COOKIE_NAME)
    if (
        not state
        or not expected_state
        or not hmac.compare_digest(state, expected_state)
        or not verify_oauth_state(state)
    ):
        raise AppException(status_code=400, detail="Invalid or expired OAuth state. Please try signing in again.")

    params = {"state": state}
    if code:
        params["code"] = code
    if error:
        params["error"] = error

    frontend_callback = f"{settings.FRONTEND_BASE_URL}/login?{urlencode(params)}"
    response = RedirectResponse(url=frontend_callback)

    # On a denied/cancelled authorization there will be no token exchange
    # to consume the state, so clear the short-lived cookie here.
    if error or not code:
        _clear_oauth_state_cookie(response)

    return response


@router.post("/google/callback", response_model=AccessTokenResponse)
async def google_callback(
    payload: TokenExchangeRequest,
    request: Request,
    response: Response,
):
    """
    Exchanges a Google authorization code only when its state matches
    the short-lived, HttpOnly state cookie established at login.
    """
    expected_state = request.cookies.get(OAUTH_STATE_COOKIE_NAME)
    if (
        not expected_state
        or not hmac.compare_digest(payload.state, expected_state)
        or not verify_oauth_state(payload.state)
    ):
        raise AppException(status_code=400, detail="Invalid or expired OAuth state. Please sign in again.")

    access_token, refresh_token, user = await exchange_code_for_session(payload.code)

    _clear_oauth_state_cookie(response)
    response.set_cookie(
        key=REFRESH_COOKIE_NAME,
        value=refresh_token,
        httponly=True,
        secure=settings.is_production,
        samesite="lax",
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
        path="/api/v1/auth",
    )

    return AccessTokenResponse(access_token=access_token, user=user)


@router.get("/me", response_model=UserResponse)
async def get_me(current_user=Depends(get_current_user)):
    """Returns the currently authenticated user's profile."""
    return current_user


@router.post("/refresh", response_model=AccessTokenResponse)
async def refresh(request: Request):
    """
    Issues a new access token using the httpOnly refresh cookie.
    Called automatically by axiosClient.js's response interceptor on
    a 401, or explicitly on app bootstrap.
    """
    refresh_token = request.cookies.get(REFRESH_COOKIE_NAME)
    access_token, user = await refresh_access_token(refresh_token)
    return AccessTokenResponse(access_token=access_token, user=user)


@router.post("/logout")
async def logout(request: Request, response: Response, current_user=Depends(get_current_user)):
    """Revokes the refresh session and clears the cookie."""
    refresh_token = request.cookies.get(REFRESH_COOKIE_NAME)
    if refresh_token:
        await revoke_session(refresh_token)

    response.delete_cookie(REFRESH_COOKIE_NAME, path="/api/v1/auth")
    return {"detail": "Logged out."}


@router.post("/dev-login", response_model=AccessTokenResponse)
async def dev_login_route(response: Response):
    """
    Developer / Demo mode login.
    Upserts a local demo user and sets authentication session tokens.
    """
    if settings.is_production:
        raise AppException(status_code=403, detail="Dev login is disabled in production.")

    access_token, refresh_token, user = await dev_login()

    response.set_cookie(
        key=REFRESH_COOKIE_NAME,
        value=refresh_token,
        httponly=True,
        secure=settings.is_production,
        samesite="lax",
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
        path="/api/v1/auth",
    )

    return AccessTokenResponse(access_token=access_token, user=user)
