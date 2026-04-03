"""Unit tests for extract_otp parser."""

import pytest

from dnse_email_otp.parser import extract_otp


class TestExtractOtp:
    def test_extract_from_body_text(self, sample_body_text: str):
        assert extract_otp(sample_body_text) == "510345"

    def test_extract_from_body_html(self, sample_body_html: str):
        assert extract_otp(sample_body_html) == "510345"

    def test_returns_none_for_empty(self):
        assert extract_otp("") is None

    def test_returns_none_no_otp(self):
        assert extract_otp("Hello world, no OTP here") is None

    def test_handles_crlf(self):
        body = "Mã OTP để xác thực giao dịch là:\r\n\r\n123456\r\n"
        assert extract_otp(body) == "123456"

    def test_handles_lf(self):
        body = "Mã OTP để xác thực giao dịch là:\n\n654321\n"
        assert extract_otp(body) == "654321"

    def test_extracts_different_otp(self):
        body = "Mã OTP để xác thực giao dịch là: 999888"
        assert extract_otp(body) == "999888"

    @pytest.mark.parametrize("text", ["12345", "1234567", "abcdef"])
    def test_ignores_non_six_digits(self, text: str):
        assert extract_otp(text) is None

    def test_standalone_six_digit_not_matched(self):
        """Standalone 6-digit number without DNSE context should NOT match."""
        assert extract_otp("Your code: 123456") is None
        assert extract_otp("123456") is None
        assert extract_otp("Phone: 098765\n123456\nEnd") is None

    def test_html_pattern_extraction(self):
        html = '<span style="letter-spacing: 25px;">777888</span>'
        assert extract_otp(html) == "777888"
