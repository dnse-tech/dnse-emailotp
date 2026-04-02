"""Gmail OTP retrieval via IMAP IDLE for DNSE."""

from dnse_email_otp.helper import wait_for_otp
from dnse_email_otp.listener import ImapListener
from dnse_email_otp.models import EmailMessage
from dnse_email_otp.parser import extract_otp

try:
    from dnse_email_otp._version import __version__
except ImportError:
    __version__ = "0.0.0"

__all__ = [
    "EmailMessage",
    "ImapListener",
    "__version__",
    "extract_otp",
    "wait_for_otp",
]
