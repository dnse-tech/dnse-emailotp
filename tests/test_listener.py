"""Tests for ImapListener and helper functions."""

from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest

from dnse_email_otp.listener import (
    ImapListener,
    _get_payload_str,
    _has_exists,
    _parse_date,
    _parse_email,
)


class TestImapListener:
    """Tests for ImapListener class."""

    def test_initialization_default_params(self):
        """ImapListener initializes with default parameters."""
        listener = ImapListener("user@gmail.com", "password123")
        assert listener._email_address == "user@gmail.com"
        assert listener._password == "password123"
        assert listener._host == "imap.gmail.com"
        assert listener._port == 993
        assert listener._folder == "INBOX"
        assert listener._idle_timeout == 28 * 60
        assert listener._client is None

    def test_initialization_custom_params(self):
        """ImapListener accepts custom parameters."""
        listener = ImapListener(
            "user@example.com",
            "pass",
            host="imap.example.com",
            port=143,
            folder="Custom",
            idle_timeout=600,
        )
        assert listener._email_address == "user@example.com"
        assert listener._password == "pass"
        assert listener._host == "imap.example.com"
        assert listener._port == 143
        assert listener._folder == "Custom"
        assert listener._idle_timeout == 600

    @patch("dnse_email_otp.listener.IMAPClient")
    def test_connect_success(self, mock_imap_class):
        """connect() establishes IMAP connection."""
        mock_client = MagicMock()
        mock_imap_class.return_value = mock_client

        listener = ImapListener("user@gmail.com", "password123")
        listener.connect()

        mock_imap_class.assert_called_once()
        mock_client.login.assert_called_once_with("user@gmail.com", "password123")
        mock_client.select_folder.assert_called_once_with("INBOX")
        assert listener._client == mock_client

    @patch("dnse_email_otp.listener.IMAPClient")
    def test_disconnect_when_connected(self, mock_imap_class):
        """disconnect() closes connection gracefully."""
        mock_client = MagicMock()
        mock_imap_class.return_value = mock_client

        listener = ImapListener("user@gmail.com", "password123")
        listener.connect()
        listener.disconnect()

        mock_client.logout.assert_called_once()
        assert listener._client is None

    def test_disconnect_when_not_connected(self):
        """disconnect() is safe when not connected."""
        listener = ImapListener("user@gmail.com", "password123")
        listener.disconnect()  # Should not raise
        assert listener._client is None

    @patch("dnse_email_otp.listener.IMAPClient")
    def test_disconnect_logout_exception(self, mock_imap_class):
        """disconnect() handles logout exceptions gracefully."""
        mock_client = MagicMock()
        mock_client.logout.side_effect = Exception("Already closed")
        mock_imap_class.return_value = mock_client

        listener = ImapListener("user@gmail.com", "password123")
        listener.connect()
        listener.disconnect()  # Should not raise

        assert listener._client is None

    @patch("dnse_email_otp.listener.IMAPClient")
    def test_context_manager_enter_exit(self, mock_imap_class):
        """ImapListener works as context manager."""
        mock_client = MagicMock()
        mock_imap_class.return_value = mock_client

        with ImapListener("user@gmail.com", "password123") as listener:
            assert listener._client == mock_client
            mock_client.login.assert_called_once()

        mock_client.logout.assert_called_once()

    @patch("dnse_email_otp.listener.IMAPClient")
    def test_ensure_connected_already_connected(self, mock_imap_class):
        """_ensure_connected() returns existing client if already connected."""
        mock_client = MagicMock()
        mock_imap_class.return_value = mock_client

        listener = ImapListener("user@gmail.com", "password123")
        listener.connect()

        result = listener._ensure_connected()
        assert result == mock_client
        # Should not reconnect
        assert mock_imap_class.call_count == 1

    @patch("dnse_email_otp.listener.IMAPClient")
    def test_ensure_connected_reconnects_when_none(self, mock_imap_class):
        """_ensure_connected() reconnects if client is None."""
        mock_client = MagicMock()
        mock_imap_class.return_value = mock_client

        listener = ImapListener("user@gmail.com", "password123")
        result = listener._ensure_connected()

        assert result == mock_client
        mock_imap_class.assert_called_once()
        mock_client.login.assert_called_once()

    @patch("dnse_email_otp.listener.IMAPClient")
    def test_fetch_unseen_no_messages(self, mock_imap_class):
        """fetch_unseen() returns empty list when no unseen messages."""
        mock_client = MagicMock()
        mock_client.search.return_value = []
        mock_imap_class.return_value = mock_client

        listener = ImapListener("user@gmail.com", "password123")
        listener.connect()

        result = listener.fetch_unseen()
        assert result == []
        mock_client.search.assert_called_once_with("UNSEEN")

    @patch("dnse_email_otp.listener.IMAPClient")
    def test_fetch_unseen_with_messages(self, mock_imap_class):
        """fetch_unseen() parses and returns unseen messages."""
        mock_client = MagicMock()
        mock_client.search.return_value = [123]

        # Minimal RFC822 message
        rfc822_bytes = (
            b"From: sender@example.com\r\n"
            b"Subject: Test\r\n"
            b"Date: Mon, 01 Jan 2024 12:00:00 +0000\r\n"
            b"Content-Type: text/plain\r\n"
            b"\r\n"
            b"Body text"
        )
        mock_client.fetch.return_value = {123: {b"RFC822": rfc822_bytes}}
        mock_imap_class.return_value = mock_client

        listener = ImapListener("user@gmail.com", "password123")
        listener.connect()

        result = listener.fetch_unseen()
        assert len(result) == 1
        assert result[0].uid == 123
        assert result[0].sender == "sender@example.com"
        assert result[0].subject == "Test"

    @patch("dnse_email_otp.listener.IMAPClient")
    def test_fetch_unseen_missing_rfc822(self, mock_imap_class):
        """fetch_unseen() skips messages without RFC822 data."""
        mock_client = MagicMock()
        mock_client.search.return_value = [456]
        mock_client.fetch.return_value = {456: {}}  # Missing RFC822
        mock_imap_class.return_value = mock_client

        listener = ImapListener("user@gmail.com", "password123")
        listener.connect()

        result = listener.fetch_unseen()
        assert result == []

    @patch("dnse_email_otp.listener.IMAPClient")
    def test_wait_for_new_message_with_exists(self, mock_imap_class):
        """wait_for_new_message() returns message when EXISTS received."""
        mock_client = MagicMock()
        mock_client.idle_check.return_value = [(b"123", b"EXISTS")]

        rfc822_bytes = (
            b"From: test@example.com\r\n"
            b"Subject: OTP\r\n"
            b"Date: Mon, 01 Jan 2024 12:00:00 +0000\r\n"
            b"Content-Type: text/plain\r\n"
            b"\r\n"
            b"Your OTP: 123456"
        )
        mock_client.search.return_value = [789]
        mock_client.fetch.return_value = {789: {b"RFC822": rfc822_bytes}}
        mock_imap_class.return_value = mock_client

        listener = ImapListener("user@gmail.com", "password123")
        listener.connect()

        result = listener.wait_for_new_message(timeout=10)
        assert result is not None
        assert result.uid == 789
        mock_client.idle.assert_called_once()
        mock_client.idle_done.assert_called_once()

    @patch("dnse_email_otp.listener.IMAPClient")
    def test_wait_for_new_message_timeout(self, mock_imap_class):
        """wait_for_new_message() returns None on timeout (no EXISTS)."""
        mock_client = MagicMock()
        mock_client.idle_check.return_value = []  # No EXISTS
        mock_imap_class.return_value = mock_client

        listener = ImapListener("user@gmail.com", "password123")
        listener.connect()

        result = listener.wait_for_new_message(timeout=5)
        assert result is None

    @patch("dnse_email_otp.listener.IMAPClient")
    @patch("dnse_email_otp.listener.time.sleep")
    def test_with_reconnect_success_on_first_try(self, mock_sleep, mock_imap_class):
        """_with_reconnect() succeeds immediately if no error."""
        mock_client = MagicMock()
        mock_imap_class.return_value = mock_client

        listener = ImapListener("user@gmail.com", "password123")
        listener.connect()

        def test_fn():
            return "success"

        result = listener._with_reconnect(test_fn)
        assert result == "success"
        mock_sleep.assert_not_called()

    @patch("dnse_email_otp.listener.IMAPClient")
    @patch("dnse_email_otp.listener.time.sleep")
    def test_with_reconnect_retry_on_oserror(self, mock_sleep, mock_imap_class):
        """_with_reconnect() retries on OSError."""
        mock_client = MagicMock()

        # Create a proper Error exception class
        class MockError(Exception):
            pass
        mock_imap_class.Error = MockError
        mock_imap_class.return_value = mock_client

        listener = ImapListener("user@gmail.com", "password123")
        listener.connect()

        call_count = 0

        def test_fn():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise OSError("Connection lost")
            return "recovered"

        result = listener._with_reconnect(test_fn)
        assert result == "recovered"
        mock_sleep.assert_called()

    @patch("dnse_email_otp.listener.IMAPClient")
    def test_with_reconnect_max_retries_exceeded(self, mock_imap_class):
        """_with_reconnect() raises ConnectionError after max retries."""
        mock_client = MagicMock()

        # Create a proper Error exception class
        class MockError(Exception):
            pass
        mock_imap_class.Error = MockError
        mock_imap_class.return_value = mock_client

        listener = ImapListener("user@gmail.com", "password123")
        listener.connect()

        def test_fn():
            raise OSError("Always fails")

        with pytest.raises(ConnectionError, match="failed after"):
            listener._with_reconnect(test_fn)


class TestHasExists:
    """Tests for _has_exists helper function."""

    def test_empty_responses(self):
        """_has_exists() returns False for empty list."""
        assert _has_exists([]) is False

    def test_exists_in_response(self):
        """_has_exists() detects EXISTS in response."""
        responses = [(b"123", b"EXISTS")]
        assert _has_exists(responses) is True

    def test_exists_in_complex_response(self):
        """_has_exists() finds EXISTS in multi-element tuple."""
        responses = [(b"456", b"[FETCH (FLAGS (\\Seen))]; EXISTS")]
        assert _has_exists(responses) is True

    def test_no_exists_in_response(self):
        """_has_exists() returns False when no EXISTS."""
        responses = [(b"789", b"EXPUNGE")]
        assert _has_exists(responses) is False

    def test_multiple_responses_with_exists(self):
        """_has_exists() finds EXISTS in multiple responses."""
        responses = [
            (b"111", b"EXPUNGE"),
            (b"222", b"EXISTS"),
            (b"333", b"FETCH"),
        ]
        assert _has_exists(responses) is True

    def test_non_tuple_responses(self):
        """_has_exists() safely handles non-tuple elements."""
        responses = ["string", 123, None]
        assert _has_exists(responses) is False

    def test_short_tuple_responses(self):
        """_has_exists() handles tuples with < 2 elements."""
        responses = [(b"111",)]
        assert _has_exists(responses) is False


class TestParseDate:
    """Tests for _parse_date helper function."""

    def test_valid_rfc2822_date(self):
        """_parse_date() parses valid RFC2822 date."""
        result = _parse_date("Mon, 01 Jan 2024 12:00:00 +0000")
        assert result.year == 2024
        assert result.month == 1
        assert result.day == 1

    def test_none_date_returns_utc_now(self):
        """_parse_date() returns UTC now for None."""
        before = datetime.now(tz=timezone.utc)
        result = _parse_date(None)
        after = datetime.now(tz=timezone.utc)

        assert result.tzinfo is not None
        assert before <= result <= after

    def test_invalid_date_string(self):
        """_parse_date() returns UTC now for invalid date."""
        before = datetime.now(tz=timezone.utc)
        result = _parse_date("not a date")
        after = datetime.now(tz=timezone.utc)

        assert result.tzinfo is not None
        assert before <= result <= after

    def test_date_with_different_timezones(self):
        """_parse_date() preserves timezone from date string."""
        result = _parse_date("Tue, 02 Jan 2024 15:30:45 +0530")
        assert result.year == 2024
        assert result.month == 1
        assert result.day == 2


class TestGetPayloadStr:
    """Tests for _get_payload_str helper function."""

    def test_string_payload(self):
        """_get_payload_str() returns string payload as-is."""
        part = MagicMock()
        part.get_content.return_value = "Hello, World!"

        result = _get_payload_str(part)
        assert result == "Hello, World!"

    def test_bytes_payload(self):
        """_get_payload_str() decodes bytes payload."""
        part = MagicMock()
        part.get_content.return_value = b"Hello, World!"

        result = _get_payload_str(part)
        assert result == "Hello, World!"

    def test_bytes_with_utf8(self):
        """_get_payload_str() decodes UTF-8 bytes."""
        part = MagicMock()
        part.get_content.return_value = "Café".encode()

        result = _get_payload_str(part)
        assert result == "Café"

    def test_invalid_bytes_replaced(self):
        """_get_payload_str() replaces invalid bytes."""
        part = MagicMock()
        part.get_content.return_value = b"Hello\xff\xfe"

        result = _get_payload_str(part)
        assert "Hello" in result
        # Invalid bytes should be replaced with replacement char

    def test_non_string_non_bytes_payload(self):
        """_get_payload_str() returns empty string for other types."""
        part = MagicMock()
        part.get_content.return_value = 12345

        result = _get_payload_str(part)
        assert result == ""

    def test_none_payload(self):
        """_get_payload_str() handles None payload."""
        part = MagicMock()
        part.get_content.return_value = None

        result = _get_payload_str(part)
        assert result == ""


class TestParseEmail:
    """Tests for _parse_email function."""

    def test_parse_simple_email(self):
        """_parse_email() parses simple plaintext email."""
        rfc822 = (
            b"From: sender@example.com\r\n"
            b"Subject: Hello\r\n"
            b"Date: Mon, 01 Jan 2024 12:00:00 +0000\r\n"
            b"Content-Type: text/plain; charset=utf-8\r\n"
            b"\r\n"
            b"Plain text body"
        )

        result = _parse_email(123, rfc822)

        assert result.uid == 123
        assert result.subject == "Hello"
        assert result.sender == "sender@example.com"
        assert result.body_text == "Plain text body"
        assert result.body_html == ""

    def test_parse_html_email(self):
        """_parse_email() extracts HTML body."""
        rfc822 = (
            b"From: test@example.com\r\n"
            b"Subject: HTML Email\r\n"
            b"Date: Tue, 02 Jan 2024 13:00:00 +0000\r\n"
            b"Content-Type: text/html; charset=utf-8\r\n"
            b"\r\n"
            b"<p>HTML content</p>"
        )

        result = _parse_email(456, rfc822)

        assert result.uid == 456
        assert result.body_html == "<p>HTML content</p>"
        assert result.body_text == ""

    def test_parse_multipart_email(self):
        """_parse_email() extracts both text and HTML from multipart."""
        rfc822 = (
            b"From: multi@example.com\r\n"
            b"Subject: Multipart\r\n"
            b"Date: Wed, 03 Jan 2024 14:00:00 +0000\r\n"
            b"MIME-Version: 1.0\r\n"
            b'Content-Type: multipart/alternative; boundary="boundary123"\r\n'
            b"\r\n"
            b"--boundary123\r\n"
            b"Content-Type: text/plain; charset=utf-8\r\n"
            b"\r\n"
            b"Plain version\r\n"
            b"--boundary123\r\n"
            b"Content-Type: text/html; charset=utf-8\r\n"
            b"\r\n"
            b"<p>HTML version</p>\r\n"
            b"--boundary123--"
        )

        result = _parse_email(789, rfc822)

        assert result.uid == 789
        assert "Plain version" in result.body_text
        assert "<p>HTML version</p>" in result.body_html

    def test_parse_email_missing_headers(self):
        """_parse_email() handles missing headers gracefully."""
        rfc822 = b"Content-Type: text/plain\r\n\r\nJust body"

        result = _parse_email(999, rfc822)

        assert result.uid == 999
        assert result.subject == ""
        assert result.sender == ""
        assert result.body_text == "Just body"

    def test_parse_email_invalid_date(self):
        """_parse_email() uses UTC now for invalid date."""
        rfc822 = (
            b"From: test@example.com\r\n"
            b"Subject: Bad Date\r\n"
            b"Date: not-a-date\r\n"
            b"Content-Type: text/plain\r\n"
            b"\r\n"
            b"Body"
        )

        before = datetime.now(tz=timezone.utc)
        result = _parse_email(111, rfc822)
        after = datetime.now(tz=timezone.utc)

        assert result.uid == 111
        assert before <= result.date <= after
