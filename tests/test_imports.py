"""Tests for package imports and public API."""


import dnse_email_otp


class TestPublicApi:
    """Tests for public API imports."""

    def test_email_message_importable(self):
        """EmailMessage is importable from package."""
        assert hasattr(dnse_email_otp, "EmailMessage")
        from dnse_email_otp import EmailMessage

        assert EmailMessage is not None

    def test_imap_listener_importable(self):
        """ImapListener is importable from package."""
        assert hasattr(dnse_email_otp, "ImapListener")
        from dnse_email_otp import ImapListener

        assert ImapListener is not None

    def test_extract_otp_importable(self):
        """extract_otp is importable from package."""
        assert hasattr(dnse_email_otp, "extract_otp")
        from dnse_email_otp import extract_otp

        assert callable(extract_otp)

    def test_wait_for_otp_importable(self):
        """wait_for_otp is importable from package."""
        assert hasattr(dnse_email_otp, "wait_for_otp")
        from dnse_email_otp import wait_for_otp

        assert callable(wait_for_otp)

    def test_version_available(self):
        """__version__ is available."""
        assert hasattr(dnse_email_otp, "__version__")
        version = dnse_email_otp.__version__
        assert isinstance(version, str)
        assert len(version) > 0

    def test_all_exports(self):
        """__all__ lists correct public API."""
        assert hasattr(dnse_email_otp, "__all__")
        all_exports = dnse_email_otp.__all__
        assert "EmailMessage" in all_exports
        assert "ImapListener" in all_exports
        assert "extract_otp" in all_exports
        assert "wait_for_otp" in all_exports
        assert "__version__" in all_exports

    def test_direct_imports_work(self):
        """Direct imports from submodules work."""
        from dnse_email_otp.helper import wait_for_otp
        from dnse_email_otp.listener import ImapListener
        from dnse_email_otp.models import EmailMessage
        from dnse_email_otp.parser import extract_otp

        assert EmailMessage is not None
        assert ImapListener is not None
        assert extract_otp is not None
        assert wait_for_otp is not None
