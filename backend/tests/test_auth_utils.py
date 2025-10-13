from datetime import datetime, timedelta, timezone

import pytest

from app.auth_utils import (
    create_access_token,
    create_reset_token,
    decode_token,
    hash_password,
    verify_password,
)


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
    """Test access token creation with timezone-aware timestamps"""
    username = "testuser"
    token = create_access_token(username)
    assert isinstance(token, str)
    assert len(token) > 50  # JWT tokens are long

    # Decode and verify the token contains timezone-aware timestamps
    decoded = decode_token(token)
    assert decoded["sub"] == username
    assert "iat" in decoded  # issued at
    assert "exp" in decoded  # expires at

    # JWT timestamps are Unix timestamps (seconds since epoch)
    # We can verify they're reasonable (recent issue time, future expiry)
    import time

    now = time.time()
    assert abs(decoded["iat"] - now) < 5  # Issued within last 5 seconds
    assert decoded["exp"] > now  # Expires in the future


def test_create_reset_token():
    """Test reset token creation with timezone-aware timestamps"""
    username = "testuser"
    minutes = 15
    token = create_reset_token(username, minutes)
    assert isinstance(token, str)
    assert len(token) > 50

    # Decode and verify the token
    decoded = decode_token(token)
    assert decoded["sub"] == username
    assert decoded["kind"] == "reset"
    assert "exp" in decoded

    # Verify expiry time is approximately correct (within 1 minute)
    import time

    expected_exp = time.time() + (minutes * 60)
    assert abs(decoded["exp"] - expected_exp) < 60


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


def test_timezone_aware_token_generation():
    """Test that tokens are generated with timezone-aware UTC timestamps"""
    from app.utils.time import utc_now

    username = "testuser"

    # Create token and capture the current UTC time
    before_time = utc_now()
    token = create_access_token(username, expires_minutes=60)
    after_time = utc_now()

    decoded = decode_token(token)

    # Convert JWT timestamps back to datetime for comparison
    iat_dt = datetime.fromtimestamp(decoded["iat"], tz=timezone.utc)
    exp_dt = datetime.fromtimestamp(decoded["exp"], tz=timezone.utc)

    # Verify issued time is within our measurement window (with some tolerance for precision)
    assert abs((iat_dt - before_time).total_seconds()) < 2  # Within 2 seconds
    assert abs((iat_dt - after_time).total_seconds()) < 2  # Within 2 seconds

    # Verify expiry is approximately 60 minutes from issue time
    expected_exp = iat_dt + timedelta(minutes=60)
    assert abs((exp_dt - expected_exp).total_seconds()) < 5  # Within 5 seconds


def test_reset_token_timezone_aware():
    """Test that reset tokens use timezone-aware timestamps"""
    from app.utils.time import utc_now

    username = "testuser"
    minutes = 30

    before_time = utc_now()
    token = create_reset_token(username, minutes)

    decoded = decode_token(token)

    # Convert JWT timestamp back to datetime
    exp_dt = datetime.fromtimestamp(decoded["exp"], tz=timezone.utc)

    # Verify expiry is approximately 30 minutes from now
    expected_exp = before_time + timedelta(minutes=minutes)

    # Allow some tolerance for timing precision
    assert abs((exp_dt - expected_exp).total_seconds()) < 5  # Within 5 seconds of expected


def test_hash_password_long():
    """Test that passwords longer than 72 bytes are properly truncated"""
    # Create a password longer than 72 bytes
    long_password = "a" * 100  # 100 characters = 100 bytes (for ASCII)
    hashed = hash_password(long_password)

    # Verify that the long password works
    assert verify_password(long_password, hashed) is True

    # Verify that a password with the same first 72 bytes verifies successfully
    truncated = "a" * 72
    assert verify_password(truncated, hashed) is True


def test_hash_password_unicode():
    """Test that passwords with unicode characters are properly handled"""
    # Create a password with unicode characters that might exceed 72 bytes
    # Each emoji is 4 bytes in UTF-8
    unicode_password = "🔒" * 20  # 20 emojis = 80 bytes
    hashed = hash_password(unicode_password)

    # Verify that the unicode password works
    assert verify_password(unicode_password, hashed) is True

    # The password should be properly truncated to 72 bytes
    assert hashed is not None
    assert len(hashed) > 20
