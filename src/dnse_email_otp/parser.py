"""OTP extraction from email body text."""

from __future__ import annotations


def extract_otp(email_body: str) -> str | None:
    """Extract OTP code from email body text.

    Args:
        email_body: Plain text email body.

    Returns:
        OTP string if found, None otherwise.

    Raises:
        NotImplementedError: Not yet implemented.
    """
    raise NotImplementedError("OTP extraction not yet implemented")
