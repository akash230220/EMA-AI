# backend/app/integrations/gmail/gmail_sync.py
"""
Gmail Synchronization and Parser.

Responsibilities:
  - fetch_new_messages: fetches recent or full inbox messages via GmailClient
  - parse_gmail_message: extracts headers, plaintext/HTML body, and attachments from Gmail payload
  - parse_email_address: splits 'Name <email@domain.com>' into name and email components
"""

from __future__ import annotations

import base64
import email.utils
import logging
import re
from datetime import datetime, timezone
from typing import Any, Optional

from app.integrations.gmail.gmail_client import GmailClient
from app.models.user import GoogleOAuthTokens

logger = logging.getLogger("ai_email_os.gmail_sync")


def parse_email_address(raw_header: str) -> tuple[Optional[str], str]:
    """
    Parses a 'From' or 'To' email header into (name, email).
    e.g. 'Jane Doe <jane@example.com>' -> ('Jane Doe', 'jane@example.com')
         'user@test.com' -> (None, 'user@test.com')
    """
    if not raw_header:
        return None, ""

    name, address = email.utils.parseaddr(raw_header)
    name_clean = name.strip() if name else None
    email_clean = address.strip().lower() if address else raw_header.strip().lower()

    return name_clean, email_clean


def _decode_body_part(data_str: str) -> str:
    """Decodes a base64url encoded body part to utf-8 text."""
    if not data_str:
        return ""
    try:
        padded = data_str + "=" * (-len(data_str) % 4)
        raw_bytes = base64.urlsafe_b64decode(padded)
        return raw_bytes.decode("utf-8", errors="replace")
    except Exception as exc:
        logger.warning("Failed to decode base64 body part: %s", exc)
        return ""


def _extract_body_and_attachments(
    payload: dict[str, Any],
) -> tuple[Optional[str], Optional[str], list[dict[str, Any]]]:
    """
    Recursively navigates MIME payload parts to extract body_text, body_html, and attachments.
    """
    body_text_parts: list[str] = []
    body_html_parts: list[str] = []
    attachments: list[dict[str, Any]] = []

    mime_type = payload.get("mimeType", "")
    body_info = payload.get("body", {})

    # Top-level body (non-multipart)
    if "data" in body_info:
        decoded = _decode_body_part(body_info["data"])
        if "text/plain" in mime_type:
            body_text_parts.append(decoded)
        elif "text/html" in mime_type:
            body_html_parts.append(decoded)

    # Multipart parts
    parts = payload.get("parts", [])
    for part in parts:
        part_mime = part.get("mimeType", "")
        part_body = part.get("body", {})
        filename = part.get("filename", "")

        # Check if part is an attachment
        if filename and part_body.get("attachmentId"):
            attachments.append({
                "id": str(part.get("partId", "")),
                "filename": filename,
                "mime_type": part_mime,
                "size_bytes": part_body.get("size"),
                "gmail_attachment_id": part_body.get("attachmentId"),
            })
        elif "data" in part_body:
            decoded = _decode_body_part(part_body["data"])
            if "text/plain" in part_mime:
                body_text_parts.append(decoded)
            elif "text/html" in part_mime:
                body_html_parts.append(decoded)
        elif part.get("parts"):
            # Recursive sub-parts
            sub_text, sub_html, sub_att = _extract_body_and_attachments(part)
            if sub_text:
                body_text_parts.append(sub_text)
            if sub_html:
                body_html_parts.append(sub_html)
            attachments.extend(sub_att)

    body_text = "\n".join(body_text_parts) if body_text_parts else None
    body_html = "\n".join(body_html_parts) if body_html_parts else None

    return body_text, body_html, attachments


def _strip_html(html_str: str) -> str:
    """Removes HTML tags to produce a clean text snippet if plaintext is missing."""
    clean = re.sub(r"<[^>]+>", " ", html_str)
    clean = re.sub(r"\s+", " ", clean)
    return clean.strip()


def parse_gmail_message(msg_payload: dict[str, Any]) -> dict[str, Any]:
    """
    Parses a raw Gmail message dict into a normalized dictionary ready
    for creating `EmailModel` and `ThreadMessage` documents.
    """
    gmail_msg_id = msg_payload["id"]
    gmail_thread_id = msg_payload.get("threadId", gmail_msg_id)
    snippet = msg_payload.get("snippet", "")
    internal_date = msg_payload.get("internalDate")

    if internal_date:
        received_at = datetime.fromtimestamp(int(internal_date) / 1000, tz=timezone.utc)
    else:
        received_at = datetime.now(timezone.utc)

    headers_list = msg_payload.get("payload", {}).get("headers", [])
    headers: dict[str, str] = {
        h["name"].lower(): h["value"] for h in headers_list if "name" in h and "value" in h
    }

    subject = headers.get("subject", "")
    from_header = headers.get("from", "")
    sender_name, sender_email = parse_email_address(from_header)

    to_header = headers.get("to", "")
    recipients = [
        email.utils.parseaddr(addr.strip())[1].lower()
        for addr in to_header.split(",")
        if addr.strip()
    ]

    body_text, body_html, attachments = _extract_body_and_attachments(
        msg_payload.get("payload", {})
    )

    # Fallback to stripped HTML if body_text is missing
    if not body_text and body_html:
        body_text = _strip_html(body_html)

    thread_message = {
        "id": gmail_msg_id,
        "sender_name": sender_name,
        "sender_email": sender_email,
        "recipients": recipients,
        "snippet": snippet,
        "body_html": body_html,
        "body_text": body_text,
        "sent_at": received_at,
        "attachments": attachments,
    }

    return {
        "gmail_message_id": gmail_msg_id,
        "gmail_thread_id": gmail_thread_id,
        "subject": subject,
        "sender_name": sender_name,
        "sender_email": sender_email,
        "snippet": snippet,
        "received_at": received_at,
        "thread": [thread_message],
        "attachments": attachments,
    }


async def fetch_new_messages(
    oauth_tokens: GoogleOAuthTokens,
    full_sync: bool = False,
    max_messages: int = 50,
) -> list[dict[str, Any]]:
    """
    Pulls recent messages from Gmail via GmailClient and parses them.

    Parameters:
      - oauth_tokens: Current user's Google OAuth tokens
      - full_sync: If True, fetches up to max_messages; if False, filters to recent inbox messages
      - max_messages: Maximum count of messages to fetch

    Returns:
      List of parsed message dicts ready for insertion into MongoDB.
    """
    client = GmailClient(oauth_tokens)
    query = None if full_sync else "label:INBOX"

    logger.info("Listing Gmail messages (full_sync=%s, max=%d)...", full_sync, max_messages)
    list_result = await client.list_messages(query=query, max_results=max_messages)
    messages_meta = list_result.get("messages", [])

    if not messages_meta:
        logger.info("No messages found during Gmail sync.")
        return []

    parsed_messages: list[dict[str, Any]] = []

    for item in messages_meta:
        msg_id = item["id"]
        try:
            raw_msg = await client.get_message(msg_id, msg_format="full")
            parsed = parse_gmail_message(raw_msg)
            parsed_messages.append(parsed)
        except Exception as exc:
            logger.warning("Failed to fetch or parse Gmail message %s: %s", msg_id, exc)

    logger.info("Successfully fetched and parsed %d messages.", len(parsed_messages))
    return parsed_messages

