"""Tests for parser and helper stubs (NotImplementedError)."""

import pytest

from dnse_email_otp.helper import wait_for_otp
from dnse_email_otp.parser import extract_otp


class TestExtractOtpStub:
    """Tests for extract_otp stub function."""

    def test_extract_otp_raises_not_implemented(self):
        """extract_otp() raises NotImplementedError."""
        with pytest.raises(NotImplementedError, match="not yet implemented"):
            extract_otp("Your OTP is: 123456")

    def test_extract_otp_with_empty_body(self):
        """extract_otp() raises NotImplementedError even with empty body."""
        with pytest.raises(NotImplementedError):
            extract_otp("")

    def test_extract_otp_with_various_inputs(self):
        """extract_otp() consistently raises NotImplementedError."""
        test_bodies = [
            "OTP: 123456",
            "Your code is 654321",
            "No OTP here",
            "12345",
            None,
        ]

        for body in test_bodies:
            with pytest.raises(NotImplementedError):
                extract_otp(body)  # type: ignore[arg-type]


class TestWaitForOtpStub:
    """Tests for wait_for_otp stub function."""

    def test_wait_for_otp_raises_not_implemented(self):
        """wait_for_otp() raises NotImplementedError."""
        with pytest.raises(NotImplementedError, match="not yet implemented"):
            wait_for_otp("user@gmail.com", "app_password")

    def test_wait_for_otp_with_custom_params(self):
        """wait_for_otp() raises NotImplementedError with custom parameters."""
        with pytest.raises(NotImplementedError):
            wait_for_otp(
                "user@gmail.com",
                "app_password",
                host="imap.example.com",
                port=143,
                folder="Custom",
                timeout=30.0,
            )

    def test_wait_for_otp_with_default_params(self):
        """wait_for_otp() raises NotImplementedError with default parameters."""
        with pytest.raises(NotImplementedError):
            wait_for_otp("test@example.com", "pass123")
