# backend/app/integrations/gmail/gmail_client.py
"""
Gmail API Client.

Direct async HTTP client for Google's Gmail REST API (v1).
Endpoints: https://gmail.googleapis.com/gmail/v1/users/me/...

Responsibilities:
  - Token freshness checking & automatic refresh
  - Listing messages and threads
  - Fetching individual message & thread payloads
  - Constructing MIME email messages (RFC 2822) & sending / replying
  - Modifying labels (marking read/unread, trash, archive)
  - Downloading attachments
"""

from __future__ import annotations

import base64
import logging
from datetime import datetime, timedelta, timezone
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any, Optional

import httpx

from app.core.config import get_settings
from app.integrations.google_oauth.oauth_client import refresh_google_access_token
from app.models.user import GoogleOAuthTokens

logger = logging.getLogger("ai_email_os.gmail_client")
settings = get_settings()

GMAIL_API_BASE = "https://gmail.googleapis.com/gmail/v1/users/me"


async def ensure_valid_token(oauth_tokens: GoogleOAuthTokens) -> str:
    """
    Checks if the access_token is expired (or close to expiring within 5 minutes).
    If expired, refreshes it using the refresh_token and updates oauth_tokens in-place.
    Returns a valid access_token string.
    """
    now = datetime.now(timezone.utc)
    # Ensure timezone aware
    expires_at = oauth_tokens.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)

    if expires_at - now < timedelta(minutes=5):
        if not oauth_tokens.refresh_token:
            raise ValueError("Gmail access token expired and no refresh_token is available.")

        logger.info("Gmail access token expiring soon/expired. Refreshing token...")
        refresh_data = await refresh_google_access_token(oauth_tokens.refresh_token)
        oauth_tokens.access_token = refresh_data["access_token"]
        oauth_tokens.expires_at = now + timedelta(seconds=refresh_data.get("expires_in", 3600))

    return oauth_tokens.access_token


class GmailClient:
    """Async client wrapper for Gmail REST API v1 operations."""

    def __init__(self, oauth_tokens: GoogleOAuthTokens):
        self.oauth_tokens = oauth_tokens

    async def _get_headers(self) -> dict[str, str]:
        token = await ensure_valid_token(self.oauth_tokens)
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

    async def list_messages(
        self,
        query: Optional[str] = None,
        label_ids: Optional[list[str]] = None,
        max_results: int = 50,
        page_token: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Calls GET /users/me/messages
        Returns dict with keys: 'messages' (list of {id, threadId}), 'nextPageToken', 'resultSizeEstimate'.
        """
        headers = await self._get_headers()
        params: dict[str, Any] = {"maxResults": max_results}
        if query:
            params["q"] = query
        if label_ids:
            params["labelIds"] = label_ids
        if page_token:
            params["pageToken"] = page_token

        async with httpx.AsyncClient(timeout=20.0) as client:
            resp = await client.get(f"{GMAIL_API_BASE}/messages", headers=headers, params=params)

        if resp.status_code != 200:
            logger.error("Gmail list_messages failed (%s): %s", resp.status_code, resp.text)
            raise ValueError(f"Failed to list Gmail messages: {resp.text}")

        return resp.json()

    async def get_message(
        self,
        message_id: str,
        msg_format: str = "full",
    ) -> dict[str, Any]:
        """
        Calls GET /users/me/messages/{id}
        Formats: 'full', 'metadata', 'minimal', 'raw'
        """
        headers = await self._get_headers()
        params = {"format": msg_format}

        async with httpx.AsyncClient(timeout=20.0) as client:
            resp = await client.get(
                f"{GMAIL_API_BASE}/messages/{message_id}",
                headers=headers,
                params=params,
            )

        if resp.status_code != 200:
            logger.error("Gmail get_message %s failed (%s): %s", message_id, resp.status_code, resp.text)
            raise ValueError(f"Failed to get Gmail message {message_id}: {resp.text}")

        return resp.json()

    async def get_thread(
        self,
        thread_id: str,
        msg_format: str = "full",
    ) -> dict[str, Any]:
        """
        Calls GET /users/me/threads/{id}
        Returns full thread object with list of message payloads.
        """
        headers = await self._get_headers()
        params = {"format": msg_format}

        async with httpx.AsyncClient(timeout=20.0) as client:
            resp = await client.get(
                f"{GMAIL_API_BASE}/threads/{thread_id}",
                headers=headers,
                params=params,
            )

        if resp.status_code != 200:
            logger.error("Gmail get_thread %s failed (%s): %s", thread_id, resp.status_code, resp.text)
            raise ValueError(f"Failed to get Gmail thread {thread_id}: {resp.text}")

        return resp.json()

    async def get_attachment(
        self,
        message_id: str,
        attachment_id: str,
    ) -> bytes:
        """
        Calls GET /users/me/messages/{messageId}/attachments/{id}
        Decodes base64url data and returns raw bytes.
        """
        headers = await self._get_headers()
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.get(
                f"{GMAIL_API_BASE}/messages/{message_id}/attachments/{attachment_id}",
                headers=headers,
            )

        if resp.status_code != 200:
            logger.error(
                "Gmail get_attachment failed msg=%s att=%s (%s): %s",
                message_id, attachment_id, resp.status_code, resp.text,
            )
            raise ValueError(f"Failed to fetch attachment: {resp.text}")

        data = resp.json().get("data", "")
        # base64url decode with padding
        padded_data = data + "=" * (-len(data) % 4)
        return base64.urlsafe_b64decode(padded_data)

    async def modify_labels(
        self,
        message_id: str,
        add_labels: Optional[list[str]] = None,
        remove_labels: Optional[list[str]] = None,
    ) -> dict[str, Any]:
        """Calls POST /users/me/messages/{id}/modify to add or remove labels (e.g. UNREAD, TRASH)."""
        headers = await self._get_headers()
        payload: dict[str, Any] = {
            "addLabelIds": add_labels or [],
            "removeLabelIds": remove_labels or [],
        }

        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(
                f"{GMAIL_API_BASE}/messages/{message_id}/modify",
                headers=headers,
                json=payload,
            )

        if resp.status_code != 200:
            logger.error("Gmail modify_labels failed for %s (%s): %s", message_id, resp.status_code, resp.text)
            raise ValueError(f"Failed to modify labels on Gmail message {message_id}: {resp.text}")

        return resp.json()

    async def send_message(
        self,
        raw_base64: str,
        thread_id: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Calls POST /users/me/messages/send
        Payload format: {"raw": "<base64url_string>", "threadId": "<optional_thread_id>"}
        """
        headers = await self._get_headers()
        body: dict[str, Any] = {"raw": raw_base64}
        if thread_id:
            body["threadId"] = thread_id

        async with httpx.AsyncClient(timeout=20.0) as client:
            resp = await client.post(
                f"{GMAIL_API_BASE}/messages/send",
                headers=headers,
                json=body,
            )

        if resp.status_code not in (200, 201):
            logger.error("Gmail send_message failed (%s): %s", resp.status_code, resp.text)
            raise ValueError(f"Failed to send email via Gmail: {resp.text}")

        return resp.json()


# ---------------------------------------------------------------------------
# High-level helper functions for sending & replying
# ---------------------------------------------------------------------------

def _create_mime_message(
    to_address: str,
    subject: str,
    body: str,
    in_reply_to: Optional[str] = None,
    references: Optional[str] = None,
    is_html: bool = False,
) -> str:
    """Creates a base64url-encoded RFC 2822 email message."""
    msg = MIMEMultipart("alternative") if is_html else MIMEText(body, "plain", "utf-8")

    if is_html:
        # If HTML, attach text fallback + html version
        part1 = MIMEText(body, "plain", "utf-8")
        part2 = MIMEText(body, "html", "utf-8")
        msg.attach(part1)
        msg.attach(part2)

    msg["To"] = to_address
    msg["Subject"] = subject

    if in_reply_to:
        msg["In-Reply-To"] = in_reply_to
    if references:
        msg["References"] = references

    raw_bytes = msg.as_bytes()
    return base64.urlsafe_b64encode(raw_bytes).decode("utf-8")


async def send_email_message(
    oauth_tokens: GoogleOAuthTokens,
    to_address: str,
    subject: str,
    body: str,
    thread_id: Optional[str] = None,
    in_reply_to: Optional[str] = None,
    is_html: bool = False,
) -> str:
    """Sends a new standalone email or response. Returns sent message ID."""
    raw_b64 = _create_mime_message(
        to_address=to_address,
        subject=subject,
        body=body,
        in_reply_to=in_reply_to,
        references=in_reply_to,
        is_html=is_html,
    )
    client = GmailClient(oauth_tokens)
    result = await client.send_message(raw_base64=raw_b64, thread_id=thread_id)
    return result.get("id", "")


async def send_reply_message(
    oauth_tokens: GoogleOAuthTokens,
    thread_id: str,
    to_address: str,
    subject: str,
    body: str,
    in_reply_to: Optional[str] = None,
) -> str:
    """
    Sends a reply message to an existing Gmail thread.
    Prefixes subject with 'Re: ' if not present.
    Returns the newly created message ID.
    """
    reply_subject = subject if subject.lower().startswith("re:") else f"Re: {subject}"
    return await send_email_message(
        oauth_tokens=oauth_tokens,
        to_address=to_address,
        subject=reply_subject,
        body=body,
        thread_id=thread_id,
        in_reply_to=in_reply_to,
    )


async def get_attachment(
    oauth_tokens: GoogleOAuthTokens,
    message_id: str,
    attachment_id: str,
) -> bytes:
    """Convenience helper to download attachment bytes."""
    client = GmailClient(oauth_tokens)
    return await client.get_attachment(message_id, attachment_id)


async def modify_message_labels(
    oauth_tokens: GoogleOAuthTokens,
    message_id: str,
    add_labels: Optional[list[str]] = None,
    remove_labels: Optional[list[str]] = None,
) -> dict[str, Any]:
    """Convenience helper to update labels on a message."""
    client = GmailClient(oauth_tokens)
    return await client.modify_labels(message_id, add_labels, remove_labels)

