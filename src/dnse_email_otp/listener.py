"""IMAP IDLE listener for real-time email arrival detection."""

from __future__ import annotations

import email as email_stdlib
import email.policy
import logging
import ssl
import time
from collections.abc import Callable
from datetime import datetime, timezone
from email.message import EmailMessage as StdlibEmailMessage
from email.utils import parsedate_to_datetime
from typing import Any

from imapclient import IMAPClient

from dnse_email_otp.models import EmailMessage

logger = logging.getLogger(__name__)

_DEFAULT_HOST = "imap.gmail.com"
_DEFAULT_PORT = 993
_DEFAULT_FOLDER = "INBOX"
_IDLE_TIMEOUT_SECS = 28 * 60  # 28 min (RFC 2177: must be < 29 min)
_MAX_FETCH_UNSEEN = 50  # cap unseen fetch to prevent OOM on neglected mailboxes
_MAX_RECONNECT_RETRIES = 3
_BACKOFF_BASE_SECS = 1.0
_BACKOFF_MAX_SECS = 30.0


class ImapListener:
    """IMAP IDLE listener for detecting new emails in real time.

    Connects to an IMAP server (Gmail by default) and uses IDLE
    to wait for new message notifications without polling.

    Args:
        email_address: Email address for IMAP login.
        password: App password (not account password when 2FA enabled).
        host: IMAP server hostname.
        port: IMAP server port.
        folder: Mailbox folder to monitor.
        idle_timeout: Seconds before re-issuing IDLE command.
    """

    def __init__(  # noqa: D107
        self,
        email_address: str,
        password: str,
        *,
        host: str = _DEFAULT_HOST,
        port: int = _DEFAULT_PORT,
        folder: str = _DEFAULT_FOLDER,
        idle_timeout: int = _IDLE_TIMEOUT_SECS,
    ) -> None:
        self._email_address = email_address
        self._password = password
        self._host = host
        self._port = port
        self._folder = folder
        self._idle_timeout = idle_timeout
        self._client: IMAPClient | None = None

    def connect(self) -> None:
        """Connect and authenticate to the IMAP server."""
        ctx = ssl.create_default_context()
        self._client = IMAPClient(self._host, port=self._port, ssl=True, ssl_context=ctx)
        self._client.login(self._email_address, self._password)
        self._client.select_folder(self._folder)  # type: ignore[reportUnknownMemberType]
        logger.info("Connected to %s:%d folder=%s", self._host, self._port, self._folder)

    def disconnect(self) -> None:
        """Disconnect from the IMAP server."""
        if self._client is None:
            return
        try:
            self._client.logout()
        except Exception:  # noqa: BLE001, S110
            logger.debug("Logout failed (connection may already be closed)")
        finally:
            self._client = None

    def _ensure_connected(self) -> IMAPClient:
        """Return active client, reconnecting if needed."""
        if self._client is None:
            self.connect()
        assert self._client is not None  # noqa: S101
        return self._client

    def wait_for_new_message(self, timeout: float = 60.0) -> EmailMessage | None:
        """Wait for a new email via IMAP IDLE.

        Args:
            timeout: Max seconds to wait for a new message.

        Returns:
            First unseen EmailMessage, or None if timeout elapsed.
        """
        return self._with_reconnect(lambda: self._idle_once(timeout))

    def _idle_once(self, timeout: float) -> EmailMessage | None:
        """Single IDLE attempt — enter idle, check for EXISTS, fetch if found."""
        client = self._ensure_connected()
        client.idle()
        try:
            responses: list[Any] = client.idle_check(timeout=timeout)  # type: ignore[reportUnknownMemberType]
        finally:
            client.idle_done()

        if _has_exists(responses):
            unseen = self.fetch_unseen()
            return unseen[0] if unseen else None
        return None

    def fetch_unseen(self) -> list[EmailMessage]:
        """Fetch all unseen messages from the selected folder.

        Returns:
            List of parsed EmailMessage instances.
        """
        client = self._ensure_connected()
        uids: list[int] = client.search("UNSEEN")  # type: ignore[reportUnknownMemberType]
        if not uids:
            return []
        uids = uids[:_MAX_FETCH_UNSEEN]

        raw_messages: dict[int, dict[bytes, Any]] = client.fetch(uids, ["RFC822"])  # type: ignore[reportUnknownMemberType]
        results: list[EmailMessage] = []
        for uid, data in raw_messages.items():
            raw_bytes: bytes | None = data.get(b"RFC822")  # type: ignore[reportAssignmentType]
            if raw_bytes is None:
                logger.warning("UID %d: no RFC822 data, skipping", uid)
                continue
            results.append(_parse_email(uid, raw_bytes))
        return results

    def _with_reconnect(
        self, fn: Callable[[], EmailMessage | None]
    ) -> EmailMessage | None:
        """Execute fn with auto-reconnect on connection errors.

        Retries up to _MAX_RECONNECT_RETRIES with exponential backoff.

        Raises:
            ConnectionError: All retry attempts exhausted.
        """
        backoff = _BACKOFF_BASE_SECS
        for attempt in range(_MAX_RECONNECT_RETRIES + 1):
            try:
                return fn()
            except (OSError, IMAPClient.Error) as exc:
                if attempt >= _MAX_RECONNECT_RETRIES:
                    msg = f"IMAP connection failed after {_MAX_RECONNECT_RETRIES} retries"
                    raise ConnectionError(msg) from exc
                logger.warning(
                    "Connection error (attempt %d/%d): %s — reconnecting in %.0fs",
                    attempt + 1,
                    _MAX_RECONNECT_RETRIES,
                    exc,
                    backoff,
                )
                self.disconnect()
                time.sleep(backoff)
                backoff = min(backoff * 2, _BACKOFF_MAX_SECS)
                self.connect()
        return None  # unreachable, satisfies type checker

    def __enter__(self) -> ImapListener:
        """Enter context manager — connect to IMAP server."""
        self.connect()
        return self

    def __exit__(self, *exc: object) -> None:
        """Exit context manager — disconnect from IMAP server."""
        self.disconnect()


def _has_exists(responses: list[Any]) -> bool:
    """Check if IDLE responses contain an EXISTS notification."""
    for resp in responses:
        if isinstance(resp, tuple) and len(resp) >= 2:  # type: ignore[reportUnknownArgumentType]
            flag = resp[1] if isinstance(resp[1], bytes) else b""
            if b"EXISTS" in flag:
                return True
    return False


def _parse_email(uid: int, raw_bytes: bytes) -> EmailMessage:
    """Parse raw RFC822 bytes into an EmailMessage dataclass."""
    msg: StdlibEmailMessage = email_stdlib.message_from_bytes(  # type: ignore[assignment]
        raw_bytes, policy=email.policy.default
    )

    subject = str(msg.get("Subject", ""))
    sender = str(msg.get("From", ""))
    date = _parse_date(msg.get("Date"))
    body_text = ""
    body_html = ""

    if msg.is_multipart():
        for part in msg.walk():
            ct = part.get_content_type()
            if ct == "text/plain" and not body_text:
                body_text = _get_payload_str(part)
            elif ct == "text/html" and not body_html:
                body_html = _get_payload_str(part)
    else:
        ct = msg.get_content_type()
        payload = _get_payload_str(msg)
        if ct == "text/html":
            body_html = payload
        else:
            body_text = payload

    return EmailMessage(
        uid=uid,
        subject=subject,
        sender=sender,
        date=date,
        body_text=body_text,
        body_html=body_html,
    )


def _get_payload_str(part: StdlibEmailMessage) -> str:
    """Extract string payload from an email part."""
    payload: Any = part.get_content()
    if isinstance(payload, str):
        return payload
    if isinstance(payload, bytes):
        return payload.decode("utf-8", errors="replace")
    return ""


def _parse_date(date_str: Any) -> datetime:
    """Parse email Date header, falling back to UTC now."""
    if date_str is None:
        return datetime.now(tz=timezone.utc)
    try:
        return parsedate_to_datetime(str(date_str))
    except (ValueError, TypeError):
        logger.warning("Failed to parse date: %s", date_str)
        return datetime.now(tz=timezone.utc)
