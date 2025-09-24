"""Tests for time utilities."""

from datetime import datetime, timedelta, timezone

import pytest

from app.utils.time import ensure_utc, to_iso_string, utc_now


class TestUtcNow:
    """Test UTC now function."""

    def test_utc_now_returns_timezone_aware(self):
        """Test that utc_now returns timezone-aware datetime."""
        result = utc_now()
        assert result.tzinfo == timezone.utc

    def test_utc_now_is_current_time(self):
        """Test that utc_now returns approximately current time."""
        before = datetime.now(timezone.utc)
        result = utc_now()
        after = datetime.now(timezone.utc)

        # Should be within a few seconds
        assert before <= result <= after


class TestEnsureUtc:
    """Test UTC timezone conversion function."""

    def test_ensure_utc_naive_datetime(self):
        """Test converting naive datetime assumes UTC."""
        naive_dt = datetime(2023, 1, 1, 12, 0, 0)
        result = ensure_utc(naive_dt)

        assert result.tzinfo == timezone.utc
        assert result.year == 2023
        assert result.month == 1
        assert result.day == 1
        assert result.hour == 12

    def test_ensure_utc_already_utc(self):
        """Test UTC datetime is returned unchanged."""
        utc_dt = datetime(2023, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        result = ensure_utc(utc_dt)

        assert result is utc_dt  # Same object
        assert result.tzinfo == timezone.utc

    def test_ensure_utc_converts_other_timezone(self):
        """Test conversion from non-UTC timezone."""
        # Eastern timezone (UTC-5)
        eastern = timezone(timedelta(hours=-5))
        eastern_dt = datetime(2023, 1, 1, 7, 0, 0, tzinfo=eastern)  # 7 AM Eastern

        result = ensure_utc(eastern_dt)

        assert result.tzinfo == timezone.utc
        assert result.hour == 12  # 7 AM Eastern = 12 PM UTC

    def test_ensure_utc_converts_positive_offset(self):
        """Test conversion from positive UTC offset timezone."""
        # Tokyo timezone (UTC+9)
        tokyo = timezone(timedelta(hours=9))
        tokyo_dt = datetime(2023, 1, 1, 21, 0, 0, tzinfo=tokyo)  # 9 PM Tokyo

        result = ensure_utc(tokyo_dt)

        assert result.tzinfo == timezone.utc
        assert result.hour == 12  # 9 PM Tokyo = 12 PM UTC


class TestToIsoString:
    """Test ISO string conversion function."""

    def test_to_iso_string_utc_datetime(self):
        """Test converting UTC datetime to ISO string."""
        utc_dt = datetime(2023, 1, 1, 12, 30, 45, tzinfo=timezone.utc)
        result = to_iso_string(utc_dt)

        assert result == "2023-01-01T12:30:45Z"

    def test_to_iso_string_with_microseconds(self):
        """Test ISO string includes microseconds when present."""
        utc_dt = datetime(2023, 1, 1, 12, 30, 45, 123456, tzinfo=timezone.utc)
        result = to_iso_string(utc_dt)

        assert result == "2023-01-01T12:30:45.123456Z"

    def test_to_iso_string_converts_timezone(self):
        """Test converting non-UTC timezone to ISO string."""
        # Eastern timezone (UTC-5)
        eastern = timezone(timedelta(hours=-5))
        eastern_dt = datetime(2023, 1, 1, 7, 30, 45, tzinfo=eastern)

        result = to_iso_string(eastern_dt)

        # Should convert to UTC (12:30:45) and format with Z
        assert result == "2023-01-01T12:30:45Z"

    def test_to_iso_string_naive_datetime_raises_error(self):
        """Test that naive datetime raises ValueError."""
        naive_dt = datetime(2023, 1, 1, 12, 30, 45)

        with pytest.raises(ValueError, match="DateTime must be timezone-aware"):
            to_iso_string(naive_dt)

    def test_to_iso_string_zero_microseconds(self):
        """Test ISO string without microseconds when zero."""
        utc_dt = datetime(2023, 1, 1, 12, 30, 45, 0, tzinfo=timezone.utc)
        result = to_iso_string(utc_dt)

        assert result == "2023-01-01T12:30:45Z"


class TestTimeUtilsIntegration:
    """Test time utilities working together."""

    def test_utc_now_to_iso_string(self):
        """Test converting current time to ISO string."""
        now = utc_now()
        result = to_iso_string(now)

        # Should end with Z and be valid format
        assert result.endswith("Z")
        assert "T" in result
        assert len(result) >= 20  # Basic format is 20 chars

    def test_ensure_utc_to_iso_string(self):
        """Test converting naive datetime through ensure_utc to ISO string."""
        naive_dt = datetime(2023, 6, 15, 14, 30, 0)
        utc_dt = ensure_utc(naive_dt)
        result = to_iso_string(utc_dt)

        assert result == "2023-06-15T14:30:00Z"
