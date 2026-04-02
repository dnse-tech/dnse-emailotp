"""High-level convenience functions combining listener and parser."""

from __future__ import annotations


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
        NotImplementedError: Stub -- not yet implemented.
    """
    raise NotImplementedError("wait_for_otp not yet implemented")
