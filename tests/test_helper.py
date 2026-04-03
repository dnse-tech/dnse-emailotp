"""Integration tests for wait_for_otp helper."""

from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest

from dnse_email_otp.helper import wait_for_otp
from dnse_email_otp.models import EmailMessage


def _make_email(body_text: str = "", body_html: str = "") -> EmailMessage:
    return EmailMessage(
        uid=1,
        subject="OTP",
        sender="no-reply@dnse.com.vn",
        date=datetime(2025, 1, 1, tzinfo=timezone.utc),
        body_text=body_text,
        body_html=body_html,
    )


class TestWaitForOtp:
    @patch("dnse_email_otp.helper.ImapListener")
    def test_returns_otp_on_success(self, mock_cls: MagicMock):
        mock_listener = MagicMock()
        mock_cls.return_value.__enter__ = MagicMock(return_value=mock_listener)
        mock_cls.return_value.__exit__ = MagicMock(return_value=False)
        mock_listener.wait_for_new_message.return_value = _make_email(
            body_text="Mã OTP để xác thực giao dịch là:\n\n510345\n"
        )

        result = wait_for_otp("user@gmail.com", "app_password")
        assert result == "510345"

    @patch("dnse_email_otp.helper.ImapListener")
    def test_raises_timeout_no_email(self, mock_cls: MagicMock):
        mock_listener = MagicMock()
        mock_cls.return_value.__enter__ = MagicMock(return_value=mock_listener)
        mock_cls.return_value.__exit__ = MagicMock(return_value=False)
        mock_listener.wait_for_new_message.return_value = None

        with pytest.raises(TimeoutError, match="No email received"):
            wait_for_otp("user@gmail.com", "app_password")

    @patch("dnse_email_otp.helper.ImapListener")
    def test_raises_timeout_no_otp(self, mock_cls: MagicMock):
        mock_listener = MagicMock()
        mock_cls.return_value.__enter__ = MagicMock(return_value=mock_listener)
        mock_cls.return_value.__exit__ = MagicMock(return_value=False)
        mock_listener.wait_for_new_message.return_value = _make_email(
            body_text="No OTP here"
        )

        with pytest.raises(TimeoutError, match="no OTP found"):
            wait_for_otp("user@gmail.com", "app_password")

    @patch("dnse_email_otp.helper.ImapListener")
    def test_passes_credentials(self, mock_cls: MagicMock):
        mock_cls.return_value.__enter__ = MagicMock(return_value=MagicMock())
        mock_cls.return_value.__exit__ = MagicMock(return_value=False)
        mock_cls.return_value.__enter__.return_value.wait_for_new_message.return_value = None

        with pytest.raises(TimeoutError):
            wait_for_otp(
                "test@example.com",
                "secret",
                host="imap.example.com",
                port=143,
                folder="Custom",
                timeout=30.0,
            )

        mock_cls.assert_called_once_with(
            "test@example.com",
            "secret",
            host="imap.example.com",
            port=143,
            folder="Custom",
        )

    @patch("dnse_email_otp.helper.ImapListener")
    def test_uses_context_manager(self, mock_cls: MagicMock):
        mock_cls.return_value.__enter__ = MagicMock(return_value=MagicMock())
        mock_cls.return_value.__exit__ = MagicMock(return_value=False)
        mock_cls.return_value.__enter__.return_value.wait_for_new_message.return_value = None

        with pytest.raises(TimeoutError):
            wait_for_otp("user@gmail.com", "app_password")

        mock_cls.return_value.__enter__.assert_called_once()
        mock_cls.return_value.__exit__.assert_called_once()

    @patch("dnse_email_otp.helper.ImapListener")
    def test_falls_back_to_html(self, mock_cls: MagicMock):
        mock_listener = MagicMock()
        mock_cls.return_value.__enter__ = MagicMock(return_value=mock_listener)
        mock_cls.return_value.__exit__ = MagicMock(return_value=False)
        mock_listener.wait_for_new_message.return_value = _make_email(
            body_text="No OTP",
            body_html='<span style="letter-spacing: 25px;">888999</span>',
        )

        result = wait_for_otp("user@gmail.com", "app_password")
        assert result == "888999"
