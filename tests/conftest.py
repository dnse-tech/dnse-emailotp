"""Shared test fixtures."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from dnse_email_otp.models import EmailMessage

_TEMPLATE_PATH = Path(__file__).parent.parent / "scripts" / "email-template.json"


@pytest.fixture
def email_template_data() -> dict[str, str]:
    """Load raw email template JSON."""
    with _TEMPLATE_PATH.open() as f:
        return json.load(f)


@pytest.fixture
def sample_body_text(email_template_data: dict[str, str]) -> str:
    """Real DNSE OTP email body_text from template."""
    return email_template_data["body_text"]


@pytest.fixture
def sample_body_html(email_template_data: dict[str, str]) -> str:
    """Real DNSE OTP email body_html from template."""
    return email_template_data["body_html"]


@pytest.fixture
def sample_email_message(sample_body_text: str, sample_body_html: str) -> EmailMessage:
    """EmailMessage with real template data."""
    return EmailMessage(
        uid=1,
        subject="OTP xác thực giao dịch",
        sender="no-reply@dnse.com.vn",
        date=datetime(2025, 1, 1, tzinfo=timezone.utc),
        body_text=sample_body_text,
        body_html=sample_body_html,
    )
