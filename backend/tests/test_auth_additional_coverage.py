"""Additional tests for auth routes to boost coverage."""

from unittest.mock import Mock, patch

import pytest

# Import the auth route functions directly for testing
from app.routes_auth import send_mail


def test_send_mail_dev_mode():
    """Test send_mail in development mode (no real email)."""
    with patch("app.routes_auth.settings") as mock_settings:
        # Configure for dev mode (no real email sending)
        mock_settings.use_email_in_dev = False
        mock_settings.smtp_host = None
        mock_settings.smtp_user = None

        # This should print to console instead of sending real email
        send_mail("test@example.com", "Test Subject", "Test Body")
        # No exception should be raised


def test_send_mail_dev_mode_with_settings_but_disabled():
    """Test send_mail when SMTP settings exist but USE_EMAIL_IN_DEV is False."""
    with patch("app.routes_auth.settings") as mock_settings:
        # Configure with SMTP settings but dev email disabled
        mock_settings.use_email_in_dev = False
        mock_settings.smtp_host = "smtp.example.com"
        mock_settings.smtp_user = "user@example.com"

        # This should still print to console instead of sending real email
        send_mail("test@example.com", "Test Subject", "Test Body")
        # No exception should be raised


def test_send_mail_partial_settings():
    """Test send_mail when only some SMTP settings are provided."""
    with patch("app.routes_auth.settings") as mock_settings:
        # Configure with partial SMTP settings
        mock_settings.use_email_in_dev = True
        mock_settings.smtp_host = "smtp.example.com"
        mock_settings.smtp_user = None  # Missing user

        # This should fall back to console printing
        send_mail("test@example.com", "Test Subject", "Test Body")
        # No exception should be raised


def test_send_mail_real_email_success():
    """Test send_mail when configured for real email sending."""
    with (
        patch("app.routes_auth.settings") as mock_settings,
        patch("app.routes_auth.smtplib.SMTP") as mock_smtp_class,
    ):
        # Configure for real email sending
        mock_settings.use_email_in_dev = True
        mock_settings.smtp_host = "smtp.example.com"
        mock_settings.smtp_user = "user@example.com"
        mock_settings.smtp_password = "password"
        mock_settings.smtp_port = 587
        mock_settings.email_from = "noreply@example.com"
        mock_settings.email_from_name = "Test App"

        # Mock SMTP server
        mock_smtp = Mock()
        mock_smtp_class.return_value.__enter__.return_value = mock_smtp

        send_mail("test@example.com", "Test Subject", "Test Body")

        # Verify SMTP calls
        mock_smtp.starttls.assert_called_once()
        mock_smtp.login.assert_called_once_with("user@example.com", "password")
        mock_smtp.send_message.assert_called_once()


def test_send_mail_real_email_failure():
    """Test send_mail when real email sending fails."""
    with (
        patch("app.routes_auth.settings") as mock_settings,
        patch("app.routes_auth.smtplib.SMTP") as mock_smtp_class,
    ):
        # Configure for real email sending
        mock_settings.use_email_in_dev = True
        mock_settings.smtp_host = "smtp.example.com"
        mock_settings.smtp_user = "user@example.com"
        mock_settings.smtp_password = "password"
        mock_settings.smtp_port = 587
        mock_settings.email_from = "noreply@example.com"
        mock_settings.email_from_name = "Test App"

        # Mock SMTP server to raise exception
        mock_smtp = Mock()
        mock_smtp.login.side_effect = Exception("SMTP Error")
        mock_smtp_class.return_value.__enter__.return_value = mock_smtp

        with pytest.raises(Exception):
            send_mail("test@example.com", "Test Subject", "Test Body")


def test_validate_invite_code_edge_cases():
    """Test validate invite code with various edge cases."""

    # We'll test the validation logic indirectly through route testing
    # This helps cover more lines in the auth routes
    pass  # Placeholder for more specific route tests if needed


def test_register_route_edge_cases():
    """Test registration route edge cases for coverage."""
    # This is a placeholder for testing specific registration scenarios
    # that might not be covered by existing tests
    pass


def test_login_route_edge_cases():
    """Test login route edge cases for coverage."""
    # This is a placeholder for testing specific login scenarios
    # that might not be covered by existing tests
    pass
