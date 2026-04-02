"""Email message data models."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class EmailMessage:
    """Parsed email message from IMAP fetch.

    Attributes:
        uid: IMAP message UID.
        subject: Email subject line.
        sender: Sender address (From header).
        date: Parsed date from email headers.
        body_text: Plain text body (empty string if none).
        body_html: HTML body (empty string if none).
    """

    uid: int
    subject: str
    sender: str
    date: datetime
    body_text: str
    body_html: str
