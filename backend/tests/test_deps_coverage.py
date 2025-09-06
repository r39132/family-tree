"""Tests for app/deps.py to increase coverage."""

from datetime import datetime, timezone
from unittest.mock import Mock, patch

import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from app.deps import _parse_timestamp, get_current_username


def test_parse_timestamp_none():
    """Test _parse_timestamp with None value."""
    result = _parse_timestamp(None)
    assert result is None


def test_parse_timestamp_firestore():
    """Test _parse_timestamp with Firestore timestamp."""
    # Mock Firestore timestamp
    mock_timestamp = Mock()
    mock_timestamp.seconds = 1609459200  # 2021-01-01 00:00:00 UTC

    result = _parse_timestamp(mock_timestamp)
    expected = datetime.fromtimestamp(1609459200, tz=timezone.utc)
    assert result == expected


def test_parse_timestamp_datetime_naive():
    """Test _parse_timestamp with naive datetime."""
    naive_dt = datetime(2021, 1, 1, 0, 0, 0)
    result = _parse_timestamp(naive_dt)
    expected = naive_dt.replace(tzinfo=timezone.utc)
    assert result == expected


def test_parse_timestamp_datetime_aware():
    """Test _parse_timestamp with timezone-aware datetime."""
    aware_dt = datetime(2021, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
    result = _parse_timestamp(aware_dt)
    assert result == aware_dt


def test_parse_timestamp_epoch_int():
    """Test _parse_timestamp with epoch seconds as int."""
    epoch = 1609459200  # 2021-01-01 00:00:00 UTC
    result = _parse_timestamp(epoch)
    expected = datetime.fromtimestamp(epoch, tz=timezone.utc)
    assert result == expected


def test_parse_timestamp_epoch_float():
    """Test _parse_timestamp with epoch seconds as float."""
    epoch = 1609459200.5
    result = _parse_timestamp(epoch)
    expected = datetime.fromtimestamp(epoch, tz=timezone.utc)
    assert result == expected


def test_parse_timestamp_iso_string():
    """Test _parse_timestamp with ISO format string."""
    iso_string = "2021-01-01T00:00:00+00:00"
    result = _parse_timestamp(iso_string)
    expected = datetime.fromisoformat(iso_string)
    assert result == expected


def test_parse_timestamp_invalid_string():
    """Test _parse_timestamp with invalid string."""
    result = _parse_timestamp("invalid-date")
    assert result is None


def test_parse_timestamp_unknown_type():
    """Test _parse_timestamp with unknown type."""
    result = _parse_timestamp(["not", "a", "timestamp"])
    assert result is None


def test_get_current_username_missing_credentials():
    """Test get_current_username when credentials are None."""
    with pytest.raises(HTTPException) as exc_info:
        get_current_username(None)

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Missing authorization header"


def test_get_current_username_invalid_token():
    """Test get_current_username with invalid token."""
    # Create mock credentials with invalid token
    mock_credentials = HTTPAuthorizationCredentials(
        scheme="Bearer", credentials="invalid.token.here"
    )

    with pytest.raises(HTTPException) as exc_info:
        get_current_username(mock_credentials)

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Could not validate credentials"


def test_get_current_username_malformed_token():
    """Test get_current_username with malformed token that causes decode exception."""
    # Create mock credentials with malformed token
    mock_credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="not.a.jwt")

    with pytest.raises(HTTPException) as exc_info:
        get_current_username(mock_credentials)

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Could not validate credentials"


def test_get_current_username_empty_payload():
    """Test get_current_username when decode_token returns None."""
    mock_credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="test.token")

    with patch("app.deps.decode_token") as mock_decode:
        mock_decode.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            get_current_username(mock_credentials)

        assert exc_info.value.status_code == 401
        assert exc_info.value.detail == "Invalid token"


def test_get_current_username_no_username():
    """Test get_current_username when payload has no sub field."""
    mock_credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="test.token")

    with patch("app.deps.decode_token") as mock_decode:
        mock_decode.return_value = {"iat": 1234567890}  # No 'sub' field

        with pytest.raises(HTTPException) as exc_info:
            get_current_username(mock_credentials)

        assert exc_info.value.status_code == 401
        assert exc_info.value.detail == "Invalid token"


def test_get_current_username_user_not_found():
    """Test get_current_username when user document doesn't exist."""
    mock_credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="test.token")

    with patch("app.deps.decode_token") as mock_decode, patch("app.deps.get_db") as mock_get_db:
        mock_decode.return_value = {"sub": "testuser", "iat": 1234567890}

        # Mock database
        mock_db = Mock()
        mock_get_db.return_value = mock_db

        # Mock user document that doesn't exist
        mock_doc = Mock()
        mock_doc.exists = False
        mock_db.collection.return_value.document.return_value.get.return_value = mock_doc

        with pytest.raises(HTTPException) as exc_info:
            get_current_username(mock_credentials)

        assert exc_info.value.status_code == 401
        assert exc_info.value.detail == "User not found"


def test_get_current_username_success():
    """Test get_current_username with valid token and user."""
    mock_credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="test.token")

    with patch("app.deps.decode_token") as mock_decode, patch("app.deps.get_db") as mock_get_db:
        mock_decode.return_value = {"sub": "testuser", "iat": 1234567890}

        # Mock database
        mock_db = Mock()
        mock_get_db.return_value = mock_db

        # Mock user document that exists
        mock_doc = Mock()
        mock_doc.exists = True
        mock_doc.to_dict.return_value = {}  # No eviction data
        mock_db.collection.return_value.document.return_value.get.return_value = mock_doc

        result = get_current_username(mock_credentials)
        assert result == "testuser"
