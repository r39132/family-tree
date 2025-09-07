"""Tests for timezone-aware datetime utilities."""

from datetime import datetime, timedelta, timezone

import pytest

from app.utils.time import ensure_utc, to_iso_string, utc_now


def test_utc_now_returns_aware_datetime():
    """Test that utc_now returns timezone-aware UTC datetime."""
    now = utc_now()

    # Should be timezone-aware
    assert now.tzinfo is not None

    # Should be UTC
    assert now.tzinfo == timezone.utc

    # Should be close to current time (within 1 second)
    expected = datetime.now(timezone.utc)
    assert abs((now - expected).total_seconds()) < 1


def test_ensure_utc_with_naive_datetime():
    """Test ensure_utc with naive datetime (assumes UTC)."""
    naive_dt = datetime(2025, 1, 1, 12, 0, 0)  # No timezone info

    result = ensure_utc(naive_dt)

    assert result.tzinfo == timezone.utc
    assert result.year == 2025
    assert result.month == 1
    assert result.day == 1
    assert result.hour == 12


def test_ensure_utc_with_utc_datetime():
    """Test ensure_utc with already UTC datetime."""
    utc_dt = datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc)

    result = ensure_utc(utc_dt)

    # Should return the same datetime
    assert result == utc_dt
    assert result.tzinfo == timezone.utc


def test_ensure_utc_with_non_utc_timezone():
    """Test ensure_utc with non-UTC timezone converts to UTC."""
    # Create a datetime in EST (UTC-5)
    est = timezone(timedelta(hours=-5))
    est_dt = datetime(2025, 1, 1, 12, 0, 0, tzinfo=est)

    result = ensure_utc(est_dt)

    # Should be converted to UTC (17:00 UTC = 12:00 EST)
    assert result.tzinfo == timezone.utc
    assert result.hour == 17  # 12 + 5 = 17
    assert result.year == 2025
    assert result.month == 1
    assert result.day == 1


def test_to_iso_string_with_utc_datetime():
    """Test to_iso_string with UTC datetime."""
    utc_dt = datetime(2025, 1, 1, 12, 30, 45, tzinfo=timezone.utc)

    result = to_iso_string(utc_dt)

    assert result == "2025-01-01T12:30:45Z"


def test_to_iso_string_with_non_utc_timezone():
    """Test to_iso_string converts non-UTC to UTC before formatting."""
    # Create datetime in EST (UTC-5)
    est = timezone(timedelta(hours=-5))
    est_dt = datetime(2025, 1, 1, 12, 0, 0, tzinfo=est)

    result = to_iso_string(est_dt)

    # Should convert to UTC (17:00) and format with Z
    assert result == "2025-01-01T17:00:00Z"


def test_to_iso_string_with_naive_datetime_raises_error():
    """Test that to_iso_string raises error for naive datetime."""
    naive_dt = datetime(2025, 1, 1, 12, 0, 0)  # No timezone info

    with pytest.raises(ValueError, match="DateTime must be timezone-aware"):
        to_iso_string(naive_dt)


def test_to_iso_string_with_microseconds():
    """Test to_iso_string handles microseconds correctly."""
    utc_dt = datetime(2025, 1, 1, 12, 30, 45, 123456, tzinfo=timezone.utc)

    result = to_iso_string(utc_dt)

    assert result == "2025-01-01T12:30:45.123456Z"


def test_utc_now_multiple_calls_increase():
    """Test that multiple calls to utc_now return increasing times."""
    time1 = utc_now()
    time2 = utc_now()

    # Second call should be at or after first call
    assert time2 >= time1

    # Both should be timezone-aware UTC
    assert time1.tzinfo == timezone.utc
    assert time2.tzinfo == timezone.utc
