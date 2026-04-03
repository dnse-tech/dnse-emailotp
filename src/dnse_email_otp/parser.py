"""OTP extraction from DNSE email body text."""

from __future__ import annotations

import logging
import re

logger = logging.getLogger(__name__)

# Vietnamese DNSE format: "Mã OTP ... là:\n\n510345"
_RE_OTP_VIET = re.compile(r"Mã OTP.*?là:\s*(\d{6})", re.DOTALL)

# HTML fallback: <span style="letter-spacing: 25px;">510345</span>
_RE_OTP_HTML = re.compile(r"letter-spacing[^>]*>(\d{6})<")


def extract_otp(email_body: str) -> str | None:
    """Extract 6-digit OTP code from a DNSE email body.

    Tries the Vietnamese plain-text pattern first, then falls back
    to the HTML letter-spacing span pattern.

    Args:
        email_body: Plain text or HTML email body.

    Returns:
        OTP string if found, None otherwise.

    """
    match = _RE_OTP_VIET.search(email_body)
    if match:
        logger.debug("OTP extracted from Vietnamese pattern")
        return match.group(1)

    match = _RE_OTP_HTML.search(email_body)
    if match:
        logger.debug("OTP extracted from HTML pattern")
        return match.group(1)

    return None
