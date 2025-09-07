"""Timezone-aware datetime utilities for consistent UTC handling across the app."""

from datetime import datetime, timezone


def utc_now() -> datetime:
    """Return current time as timezone-aware UTC datetime.

    Replacement for datetime.utcnow() which is naive and deprecated in Python 3.12+.
    All application code should use this function for current time.

    Returns:
        datetime: Current time in UTC with timezone info
    """
    return datetime.now(timezone.utc)


def ensure_utc(dt: datetime) -> datetime:
    """Ensure a datetime is timezone-aware UTC.

    Args:
        dt: Input datetime (naive or aware)

    Returns:
        datetime: UTC timezone-aware datetime

    Raises:
        ValueError: If input datetime has non-UTC timezone
    """
    if dt.tzinfo is None:
        # Naive datetime - assume UTC
        return dt.replace(tzinfo=timezone.utc)
    elif dt.tzinfo == timezone.utc:
        # Already UTC
        return dt
    else:
        # Convert from other timezone to UTC
        return dt.astimezone(timezone.utc)


def to_iso_string(dt: datetime) -> str:
    """Convert datetime to ISO8601 string with Z suffix for UTC.

    Args:
        dt: Timezone-aware datetime

    Returns:
        str: ISO8601 formatted string ending with 'Z'
    """
    if dt.tzinfo is None:
        raise ValueError("DateTime must be timezone-aware")

    # Convert to UTC if not already
    utc_dt = dt.astimezone(timezone.utc)

    # Format as ISO8601 with Z suffix
    return utc_dt.isoformat().replace("+00:00", "Z")
