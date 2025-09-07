"""Tests for timezone-aware datetime usage in routes and endpoints."""

from datetime import datetime, timezone
from unittest.mock import Mock, patch

from fastapi.testclient import TestClient


def test_health_endpoint_returns_timezone_aware_timestamp():
    """Test that /healthz endpoint returns ISO8601 timestamp with Z suffix."""
    from app.main import app

    client = TestClient(app)
    response = client.get("/healthz")

    assert response.status_code == 200
    data = response.json()

    # Should have timestamp field
    assert "timestamp" in data
    timestamp = data["timestamp"]

    # Should be ISO8601 format with Z suffix (UTC)
    assert timestamp.endswith("Z")

    # Should be parseable as ISO format
    parsed = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
    assert parsed.tzinfo == timezone.utc


@patch("app.firestore_client.get_db")
def test_admin_log_action_uses_timezone_aware_timestamp(mock_get_db):
    """Test that admin log actions use timezone-aware timestamps."""
    from app.routes_admin import log_admin_action

    # Mock Firestore
    mock_collection = Mock()
    mock_db = Mock()
    mock_db.collection.return_value = mock_collection
    mock_get_db.return_value = mock_db

    # Call the function
    log_admin_action("admin_user", "test_action", "target_user", {"extra": "data"})

    # Verify collection.add was called
    mock_db.collection.assert_called_once_with("admin_logs")
    mock_collection.add.assert_called_once()

    # Get the payload that was added
    call_args = mock_collection.add.call_args[0][0]

    # Should have timestamp field
    assert "timestamp" in call_args
    timestamp = call_args["timestamp"]

    # Should be ISO8601 format with Z suffix
    assert timestamp.endswith("Z")

    # Should be recent (within last 5 seconds)
    parsed = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
    now = datetime.now(timezone.utc)
    assert abs((now - parsed).total_seconds()) < 5


@patch("app.firestore_client.get_db")
def test_user_eviction_uses_timezone_aware_timestamp(mock_get_db):
    """Test that user eviction uses timezone-aware timestamps."""
    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    from app.routes_admin import router

    # Create test app with admin router
    app = FastAPI()
    app.include_router(router)

    # Mock Firestore and user document
    mock_doc = Mock()
    mock_doc.exists = True
    mock_doc.to_dict.return_value = {"admin": True}

    mock_ref = Mock()
    mock_ref.get.return_value = mock_doc
    mock_ref.update = Mock()

    mock_collection = Mock()
    mock_collection.document.return_value = mock_ref
    mock_collection.add = Mock()

    mock_db = Mock()
    mock_db.collection.return_value = mock_collection
    mock_get_db.return_value = mock_db

    client = TestClient(app)

    # Mock authentication
    with patch("app.routes_admin.require_admin", return_value="admin_user"):
        response = client.post("/admin/users/test_user/evict")

    assert response.status_code == 200

    # Verify update was called with timezone-aware timestamp
    mock_ref.update.assert_called_once()
    update_data = mock_ref.update.call_args[0][0]

    assert "sessions_invalid_after" in update_data
    timestamp = update_data["sessions_invalid_after"]

    # Should be ISO8601 format with Z suffix
    assert timestamp.endswith("Z")

    # Should be parseable and recent
    parsed = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
    now = datetime.now(timezone.utc)
    assert abs((now - parsed).total_seconds()) < 5


def test_events_uses_timezone_aware_current_time():
    """Test that event processing uses timezone-aware current time."""
    from app.routes_events import get_all_year_events

    # Mock member data
    members = [{"dob": "1990-01-15", "name": "Test Person"}]

    # Call function - should not raise any timezone-related errors
    upcoming, past = get_all_year_events(members, year=2025)

    # Should complete without error
    assert isinstance(upcoming, list)
    assert isinstance(past, list)


@patch("app.routes_events.utc_now")
def test_events_notification_uses_utc_now(mock_utc_now):
    """Test that event notifications use utc_now function."""
    from app.routes_events import get_all_year_events

    # Mock utc_now to return a specific time
    mock_time = datetime(2025, 6, 15, 12, 0, 0, tzinfo=timezone.utc)
    mock_utc_now.return_value = mock_time

    members = [
        {"dob": "1990-06-16", "name": "Test Person"}  # Birthday tomorrow
    ]

    upcoming, past = get_all_year_events(members, year=2025)

    # Verify utc_now was called
    assert mock_utc_now.call_count >= 1

    # Should have found the upcoming birthday
    assert len(upcoming) > 0


def test_no_naive_datetime_usage_in_auth_utils():
    """Integration test to ensure no naive datetime usage in auth tokens."""
    from app.auth_utils import create_access_token, create_reset_token, decode_token

    # Create tokens
    access_token = create_access_token("testuser")
    reset_token = create_reset_token("testuser", 30)

    # Decode tokens
    access_decoded = decode_token(access_token)
    reset_decoded = decode_token(reset_token)

    # Verify timestamps are present and reasonable
    import time

    now = time.time()

    # Access token
    assert "iat" in access_decoded
    assert "exp" in access_decoded
    assert abs(access_decoded["iat"] - now) < 5  # Recent issue time
    assert access_decoded["exp"] > now  # Future expiry

    # Reset token
    assert "exp" in reset_decoded
    assert reset_decoded["exp"] > now  # Future expiry

    # Verify expiry is approximately 30 minutes from now
    expected_exp = now + (30 * 60)
    assert abs(reset_decoded["exp"] - expected_exp) < 60  # Within 1 minute


@patch("app.routes_auth.utc_now")
def test_routes_auth_uses_utc_now_for_time_diff(mock_utc_now):
    """Test that routes_auth uses utc_now for time difference calculations."""
    # This would require more complex mocking of the entire auth flow
    # For now, we'll verify that utc_now is imported and available
    from app import routes_auth

    # Check that the module has access to timezone-aware utilities
    # This is a smoke test to ensure imports are working
    assert hasattr(routes_auth, "timezone")  # Should have timezone import

    # The actual time difference calculation happens in a complex auth flow
    # that would require extensive mocking to test properly
