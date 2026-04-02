"""Tests for EmailMessage dataclass."""

from datetime import datetime, timezone

import pytest

from dnse_email_otp.models import EmailMessage


class TestEmailMessage:
    """Tests for EmailMessage frozen dataclass."""

    def test_creation_with_all_fields(self):
        """EmailMessage can be created with all required fields."""
        now = datetime.now(tz=timezone.utc)
        msg = EmailMessage(
            uid=123,
            subject="Test Subject",
            sender="sender@example.com",
            date=now,
            body_text="Plain text body",
            body_html="<p>HTML body</p>",
        )
        assert msg.uid == 123
        assert msg.subject == "Test Subject"
        assert msg.sender == "sender@example.com"
        assert msg.date == now
        assert msg.body_text == "Plain text body"
        assert msg.body_html == "<p>HTML body</p>"

    def test_creation_with_empty_bodies(self):
        """EmailMessage allows empty body fields."""
        now = datetime.now(tz=timezone.utc)
        msg = EmailMessage(
            uid=456,
            subject="Empty Bodies",
            sender="test@example.com",
            date=now,
            body_text="",
            body_html="",
        )
        assert msg.body_text == ""
        assert msg.body_html == ""

    def test_immutability(self):
        """EmailMessage is immutable (frozen=True)."""
        now = datetime.now(tz=timezone.utc)
        msg = EmailMessage(
            uid=789,
            subject="Immutable",
            sender="frozen@example.com",
            date=now,
            body_text="Original",
            body_html="<p>Original</p>",
        )
        with pytest.raises(AttributeError):
            msg.subject = "Modified"  # type: ignore[misc]

    def test_equality(self):
        """EmailMessage equality comparison works."""
        now = datetime.now(tz=timezone.utc)
        msg1 = EmailMessage(
            uid=100,
            subject="Same",
            sender="same@example.com",
            date=now,
            body_text="text",
            body_html="html",
        )
        msg2 = EmailMessage(
            uid=100,
            subject="Same",
            sender="same@example.com",
            date=now,
            body_text="text",
            body_html="html",
        )
        assert msg1 == msg2

    def test_inequality(self):
        """EmailMessage inequality comparison works."""
        now = datetime.now(tz=timezone.utc)
        msg1 = EmailMessage(
            uid=100,
            subject="Different",
            sender="a@example.com",
            date=now,
            body_text="text1",
            body_html="html1",
        )
        msg2 = EmailMessage(
            uid=200,
            subject="Different",
            sender="a@example.com",
            date=now,
            body_text="text1",
            body_html="html1",
        )
        assert msg1 != msg2
