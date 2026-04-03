"""Smoke tests verifying parser and helper are callable with expected types."""

from dnse_email_otp.helper import wait_for_otp
from dnse_email_otp.parser import extract_otp


class TestExtractOtpSmoke:
    def test_returns_none_for_empty(self):
        result = extract_otp("")
        assert result is None

    def test_returns_str_when_matched(self):
        result = extract_otp("Mã OTP để xác thực giao dịch là: 123456")
        assert isinstance(result, str)


class TestWaitForOtpSmoke:
    def test_function_is_callable(self):
        assert callable(wait_for_otp)
