# backend/app/integrations/google_oauth/oauth_client.py
"""
Google OAuth 2.0 Integration Client.

Responsibilities:
  - build_authorization_url: Constructs the Google OAuth 2.0 consent screen URL
  - exchange_authorization_code: Exchanges one-time auth code for access & refresh tokens
  - get_google_user_info: Retrieves profile info (sub, email, name, picture) via Google OpenID/userinfo
  - refresh_google_access_token: Uses long-lived refresh token to obtain a fresh access token
  - revoke_google_token: Revokes an access or refresh token with Google
"""

from __future__ import annotations

import logging
from typing import Any, Optional
from urllib.parse import urlencode

import httpx

from app.core.config import get_settings

logger = logging.getLogger("ai_email_os.google_oauth")
settings = get_settings()

GOOGLE_AUTH_BASE_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v3/userinfo"
GOOGLE_REVOKE_URL = "https://oauth2.googleapis.com/revoke"


def build_authorization_url(
    scopes: Optional[list[str]] = None,
    redirect_uri: Optional[str] = None,
    state: Optional[str] = None,
    prompt: str = "select_account consent",
    access_type: str = "offline",
) -> str:
    """
    Constructs the Google OAuth 2.0 authorization URL for redirecting the user to consent screen.

    Parameters:
      - scopes: List of OAuth scope strings (defaults to settings.GOOGLE_OAUTH_SCOPES)
      - redirect_uri: OAuth callback URI (defaults to settings.GOOGLE_OAUTH_REDIRECT_URI)
      - state: Optional CSRF token or client state to preserve across redirect
      - prompt: 'select_account consent' forces consent screen & account selector to guarantee refresh token
      - access_type: 'offline' ensures Google issues a refresh_token

    Returns:
      Full URL string for Google's consent screen.
    """
    selected_scopes = scopes or settings.GOOGLE_OAUTH_SCOPES
    selected_redirect_uri = redirect_uri or settings.GOOGLE_OAUTH_REDIRECT_URI

    params = {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "redirect_uri": selected_redirect_uri,
        "response_type": "code",
        "scope": " ".join(selected_scopes),
        "access_type": access_type,
        "prompt": prompt,
        "include_granted_scopes": "true",
    }

    if state:
        params["state"] = state

    url = f"{GOOGLE_AUTH_BASE_URL}?{urlencode(params)}"
    logger.debug("Generated Google OAuth URL with redirect_uri=%s", selected_redirect_uri)
    return url


async def exchange_authorization_code(
    code: str,
    redirect_uri: Optional[str] = None,
) -> dict[str, Any]:
    """
    Exchanges an authorization code for Google access and refresh tokens.

    Parameters:
      - code: Authorization code received from Google's redirect
      - redirect_uri: The same redirect_uri used in authorization request

    Returns:
      Dictionary containing:
        - access_token (str)
        - refresh_token (str, optional)
        - expires_in (int)
        - token_type (str)
        - scope (str)
        - id_token (str, optional)
    """
    selected_redirect_uri = redirect_uri or settings.GOOGLE_OAUTH_REDIRECT_URI

    payload = {
        "code": code,
        "client_id": settings.GOOGLE_CLIENT_ID,
        "client_secret": settings.GOOGLE_CLIENT_SECRET,
        "redirect_uri": selected_redirect_uri,
        "grant_type": "authorization_code",
    }

    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.post(GOOGLE_TOKEN_URL, data=payload)

    if response.status_code != 200:
        logger.error(
            "Failed Google token exchange. Status: %s, Body: %s",
            response.status_code,
            response.text,
        )
        raise ValueError(
            f"Google token exchange failed ({response.status_code}): {response.text}"
        )

    tokens = response.json()
    logger.info("Successfully exchanged Google authorization code for tokens.")
    return tokens


async def get_google_user_info(access_token: str) -> dict[str, Any]:
    """
    Fetches the authenticated user's profile info from Google's UserInfo endpoint.

    Parameters:
      - access_token: Valid Google access token

    Returns:
      Dictionary containing:
        - sub (str): Unique Google user identifier
        - email (str): User's primary email address
        - email_verified (bool)
        - name (str): Full display name
        - picture (str, optional): URL to profile photo
        - given_name (str, optional)
        - family_name (str, optional)
    """
    headers = {"Authorization": f"Bearer {access_token}"}

    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(GOOGLE_USERINFO_URL, headers=headers)

    if response.status_code != 200:
        logger.error(
            "Failed fetching Google user info. Status: %s, Body: %s",
            response.status_code,
            response.text,
        )
        raise ValueError(
            f"Failed to fetch Google user info ({response.status_code}): {response.text}"
        )

    user_info = response.json()
    logger.debug("Retrieved user info for sub=%s email=%s", user_info.get("sub"), user_info.get("email"))
    return user_info


async def refresh_google_access_token(refresh_token: str) -> dict[str, Any]:
    """
    Refreshes an expired Google access token using the stored refresh token.

    Parameters:
      - refresh_token: Google OAuth 2.0 refresh token

    Returns:
      Dictionary containing:
        - access_token (str)
        - expires_in (int)
        - token_type (str)
        - scope (str, optional)
    """
    payload = {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "client_secret": settings.GOOGLE_CLIENT_SECRET,
        "refresh_token": refresh_token,
        "grant_type": "refresh_token",
    }

    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.post(GOOGLE_TOKEN_URL, data=payload)

    if response.status_code != 200:
        logger.error(
            "Failed to refresh Google access token. Status: %s, Body: %s",
            response.status_code,
            response.text,
        )
        raise ValueError(
            f"Failed to refresh Google access token ({response.status_code}): {response.text}"
        )

    tokens = response.json()
    logger.info("Successfully refreshed Google access token.")
    return tokens


async def revoke_google_token(token: str) -> bool:
    """
    Revokes a Google access or refresh token.
    Called when a user explicitly disconnects their Google account.

    Parameters:
      - token: Access or refresh token to revoke

    Returns:
      True if revocation succeeded or Google returned 200 OK.
    """
    params = {"token": token}
    headers = {"Content-Type": "application/x-www-form-urlencoded"}

    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.post(GOOGLE_REVOKE_URL, params=params, headers=headers)

    if response.status_code == 200:
        logger.info("Successfully revoked Google token.")
        return True
    else:
        logger.warning(
            "Google token revocation returned non-200 (%s): %s",
            response.status_code,
            response.text,
        )
        return False

