"""High-level convenience functions combining listener and parser."""

from __future__ import annotations

import logging

from dnse_email_otp.listener import ImapListener
from dnse_email_otp.parser import extract_otp

logger = logging.getLogger(__name__)


def wait_for_otp(
    email_address: str,
    app_password: str,
    *,
    host: str = "imap.gmail.com",
    port: int = 993,
    folder: str = "INBOX",
    timeout: float = 60.0,
) -> str:
    """Wait for OTP email and extract code.

    Connects to IMAP, waits for new email via IDLE,
    extracts OTP from body.

    Args:
        email_address: Gmail address.
        app_password: Gmail app password.
        host: IMAP host.
        port: IMAP port.
        folder: Mailbox folder.
        timeout: Max seconds to wait.

    Returns:
        OTP code string.

    Raises:
        TimeoutError: No OTP email within timeout.
    """
    with ImapListener(
        email_address, app_password, host=host, port=port, folder=folder
    ) as listener:
        msg = listener.wait_for_new_message(timeout=timeout)
        if msg is None:
            logger.warning("No email received within %.0fs", timeout)
            raise TimeoutError("No email received within timeout")

        otp = extract_otp(msg.body_text) or extract_otp(msg.body_html)
        if otp is None:
            logger.warning("Email received but no OTP found (subject=%s)", msg.subject)
            raise TimeoutError("Email received but no OTP found")

        logger.info("OTP extracted successfully")
        return otp
