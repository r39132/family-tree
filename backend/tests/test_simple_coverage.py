"""Simple, targeted tests to increase coverage without complex mocking."""

from datetime import datetime
from unittest.mock import patch

from app.routes_auth import send_mail
from app.routes_events import calculate_age, parse_date
from app.routes_tree import _name_key


def test_send_mail_with_dev_mode():
    """Test send_mail function in development mode."""
    with patch("app.routes_auth.settings") as mock_settings:
        mock_settings.use_email_in_dev = False
        mock_settings.smtp_host = None
        mock_settings.smtp_user = None

        # Should not raise exception in dev mode - just print
        send_mail("test@example.com", "Test Subject", "Test Body")


def test_send_mail_with_production_config():
    """Test send_mail function configuration check."""
    with patch("app.routes_auth.settings") as mock_settings:
        # Configure for production but don't actually send
        mock_settings.use_email_in_dev = True
        mock_settings.smtp_host = "smtp.example.com"
        mock_settings.smtp_user = "user@example.com"
        mock_settings.smtp_port = 587
        mock_settings.smtp_password = "password"
        mock_settings.email_from = "from@example.com"
        mock_settings.email_from_name = "Test App"

        # Mock SMTP to avoid actual email sending
        with patch("app.routes_auth.smtplib.SMTP") as mock_smtp:
            mock_server = mock_smtp.return_value.__enter__.return_value

            send_mail("test@example.com", "Test Subject", "Test Body")

            # Verify SMTP was called correctly
            mock_smtp.assert_called_once_with("smtp.example.com", 587)
            mock_server.starttls.assert_called_once()
            mock_server.login.assert_called_once_with("user@example.com", "password")


def test_name_key_function():
    """Test the _name_key utility function from routes_tree."""
    # Test normal cases
    assert _name_key("John", "Doe") == "john|doe"
    assert _name_key("Mary-Jane", "Smith-Williams") == "mary-jane|smith-williams"

    # Test with spaces
    assert _name_key(" John ", " Doe ") == "john|doe"

    # Test with empty strings
    assert _name_key("", "Doe") == "|doe"
    assert _name_key("John", "") == "john|"
    assert _name_key("", "") == "|"


def test_calculate_age_comprehensive():
    """Test calculate_age with comprehensive cases."""
    current_date = datetime(2024, 6, 15)

    # Test different formats
    assert calculate_age("1990-01-01", current_date) == 34
    assert calculate_age("01/01/1990", current_date) == 34

    # Test birthday timing
    assert calculate_age("1990-12-25", current_date) == 33  # Birthday not yet occurred
    assert calculate_age("1990-03-15", current_date) == 34  # Birthday already occurred

    # Test edge cases
    assert calculate_age("invalid-date", current_date) == 0
    assert calculate_age("1990-13-01", current_date) == 0  # Invalid month
    assert calculate_age("", current_date) == 0


def test_parse_date_comprehensive():
    """Test parse_date with comprehensive cases."""
    # Test valid formats
    result = parse_date("2024-01-15")
    assert result == datetime(2024, 1, 15)

    result = parse_date("01/15/2024")
    assert result == datetime(2024, 1, 15)

    # Test error cases
    try:
        parse_date("invalid-date")
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "Unable to parse date" in str(e)


def test_age_calculation_edge_cases():
    """Test age calculation edge cases."""
    # Test leap year
    current_date = datetime(2024, 2, 29)
    assert calculate_age("2000-02-29", current_date) == 24

    # Test same day
    assert calculate_age("2024-02-29", current_date) == 0

    # Test very old dates
    assert calculate_age("1900-01-01", current_date) == 124


def test_date_parsing_edge_cases():
    """Test date parsing with edge cases."""
    # Test boundary dates
    result = parse_date("2024-12-31")
    assert result == datetime(2024, 12, 31)

    result = parse_date("2024-01-01")
    assert result == datetime(2024, 1, 1)

    # Test different separators
    try:
        parse_date("2024.01.01")  # Unsupported format
        assert False, "Should have raised ValueError"
    except ValueError:
        pass  # Expected


def test_email_sending_error_handling():
    """Test email sending error handling."""
    with patch("app.routes_auth.settings") as mock_settings:
        mock_settings.use_email_in_dev = True
        mock_settings.smtp_host = "smtp.example.com"
        mock_settings.smtp_user = "user@example.com"
        mock_settings.smtp_port = 587
        mock_settings.smtp_password = "password"
        mock_settings.email_from = "from@example.com"
        mock_settings.email_from_name = "Test App"

        # Mock SMTP to raise an exception
        with patch("app.routes_auth.smtplib.SMTP") as mock_smtp:
            mock_smtp.side_effect = Exception("SMTP Connection Failed")

            try:
                send_mail("test@example.com", "Test Subject", "Test Body")
                assert False, "Should have raised exception"
            except Exception as e:
                assert "SMTP Connection Failed" in str(e)


def test_name_key_with_various_characters():
    """Test _name_key with various character combinations."""
    # Test with hyphens
    assert _name_key("Mary-Jane", "Smith-Williams") == "mary-jane|smith-williams"

    # Test with mixed case
    assert _name_key("JoHn", "DoE") == "john|doe"

    # Test with numbers (if they exist in names)
    assert _name_key("John2", "Doe3") == "john2|doe3"


def test_utility_functions_integration():
    """Test utility functions working together."""
    # Test date parsing then age calculation
    parsed_date = parse_date("1990-06-15")
    current = datetime(2024, 6, 16)  # Day after birthday

    # Verify the parsed date is correct
    assert parsed_date.year == 1990
    assert parsed_date.month == 6
    assert parsed_date.day == 15

    # Convert back to string for age calculation
    age = calculate_age("1990-06-15", current)
    assert age == 34  # Birthday just passed
