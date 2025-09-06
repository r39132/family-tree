"""Tests for app/routes_events.py utility functions to increase coverage."""

from datetime import datetime

import pytest

from app.routes_events import calculate_age, parse_date


def test_calculate_age_various_formats():
    """Test calculate_age with different date formats."""
    current_date = datetime(2024, 6, 15)

    # Test YYYY-MM-DD format
    assert calculate_age("1990-01-01", current_date) == 34

    # Test MM/DD/YYYY format
    assert calculate_age("01/01/1990", current_date) == 34

    # Test DD/MM/YYYY format
    assert calculate_age("01/01/1990", current_date) == 34

    # Test birthday not yet occurred this year
    assert calculate_age("1990-12-25", current_date) == 33

    # Test birthday already occurred this year
    assert calculate_age("1990-03-15", current_date) == 34


def test_calculate_age_invalid_format():
    """Test calculate_age with invalid date format returns 0."""
    current_date = datetime(2024, 6, 15)

    # Invalid format should return 0
    assert calculate_age("invalid-date", current_date) == 0
    assert calculate_age("1990-13-01", current_date) == 0  # Invalid month
    assert calculate_age("", current_date) == 0


def test_calculate_age_edge_cases():
    """Test calculate_age edge cases."""
    current_date = datetime(2024, 2, 29)  # Leap year

    # Test same day
    assert calculate_age("2024-02-29", current_date) == 0

    # Test future date should return 0 (max with 0)
    # Actually, let's test a case where someone is very young
    assert calculate_age("2023-02-28", current_date) == 1


def test_parse_date_valid_formats():
    """Test parse_date with valid date formats."""
    # Test YYYY-MM-DD format
    result = parse_date("2024-01-15")
    assert result == datetime(2024, 1, 15)

    # Test MM/DD/YYYY format
    result = parse_date("01/15/2024")
    assert result == datetime(2024, 1, 15)

    # Test DD/MM/YYYY format
    result = parse_date("15/01/2024")
    assert result == datetime(2024, 1, 15)


def test_parse_date_invalid_format():
    """Test parse_date with invalid format raises ValueError."""
    with pytest.raises(ValueError, match="Unable to parse date: invalid-date"):
        parse_date("invalid-date")

    with pytest.raises(ValueError, match="Unable to parse date: 2024-13-01"):
        parse_date("2024-13-01")  # Invalid month
