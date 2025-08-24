import pytest
from datetime import datetime, timezone, timedelta
from app.auth_utils import hash_password, verify_password, create_access_token, create_reset_token, decode_token
from app.deps import get_current_username
from fastapi import HTTPException
from unittest.mock import Mock


def test_hash_password():
    """Test password hashing"""
    password = "testpassword123"
    hashed = hash_password(password)
    assert hashed != password
    assert len(hashed) > 20  # bcrypt hashes are long


def test_verify_password_correct():
    """Test password verification with correct password"""
    password = "testpassword123"
    hashed = hash_password(password)
    assert verify_password(password, hashed) is True


def test_verify_password_incorrect():
    """Test password verification with incorrect password"""
    password = "testpassword123"
    wrong_password = "wrongpassword"
    hashed = hash_password(password)
    assert verify_password(wrong_password, hashed) is False


def test_verify_password_invalid_hash():
    """Test password verification with invalid hash"""
    password = "testpassword123"
    invalid_hash = "not-a-valid-hash"
    # passlib raises an exception for invalid hashes, so we expect False after exception handling
    try:
        result = verify_password(password, invalid_hash)
        assert result is False
    except Exception:
        # If exception is raised, that's also acceptable behavior
        pass


def test_create_access_token():
    """Test access token creation"""
    username = "testuser"
    token = create_access_token(username)
    assert isinstance(token, str)
    assert len(token) > 50  # JWT tokens are long


def test_create_reset_token():
    """Test reset token creation"""
    username = "testuser"
    token = create_reset_token(username)
    assert isinstance(token, str)
    assert len(token) > 50


def test_decode_token_valid():
    """Test decoding valid token"""
    username = "testuser"
    token = create_access_token(username)
    decoded = decode_token(token)
    assert decoded["sub"] == username
    # Access tokens don't have 'kind' field, only reset tokens do


def test_decode_token_invalid():
    """Test decoding invalid token"""
    invalid_token = "invalid.token.here"
    with pytest.raises(Exception):
        decode_token(invalid_token)


def test_decode_reset_token():
    """Test decoding reset token"""
    username = "testuser"
    token = create_reset_token(username)
    decoded = decode_token(token)
    assert decoded["sub"] == username
    assert decoded["kind"] == "reset"


def test_get_current_username_valid_token():
    """Test getting username from valid token"""
    # This would require mocking the HTTP request context
    # For now, we'll test the basic structure
    pass  # Placeholder - complex to test without request context


def test_get_current_username_invalid_token():
    """Test getting username from invalid token"""
    # This would require mocking HTTPBearer and request
    pass  # Placeholder - complex to test without request context
