"""Gmail API Integration Package."""

from app.integrations.gmail.gmail_client import (
    GmailClient,
    ensure_valid_token,
    get_attachment,
    modify_message_labels,
    send_email_message,
    send_reply_message,
)
from app.integrations.gmail.gmail_sync import (
    fetch_new_messages,
    parse_email_address,
    parse_gmail_message,
)

__all__ = [
    "GmailClient",
    "ensure_valid_token",
    "send_reply_message",
    "send_email_message",
    "get_attachment",
    "modify_message_labels",
    "fetch_new_messages",
    "parse_gmail_message",
    "parse_email_address",
]

