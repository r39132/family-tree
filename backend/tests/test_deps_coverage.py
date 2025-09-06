"""Tests for app/deps.py to increase coverage."""

import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from app.deps import get_current_username


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
    assert exc_info.value.detail == "Invalid token"


def test_get_current_username_malformed_token():
    """Test get_current_username with malformed token that causes decode exception."""
    # Create mock credentials with malformed token
    mock_credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="not.a.jwt")

    with pytest.raises(HTTPException) as exc_info:
        get_current_username(mock_credentials)

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Invalid token"
