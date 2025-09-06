"""Tests for routes_events.py API endpoints to increase coverage."""

from fastapi.testclient import TestClient

import app.routes_auth as routes_auth
import app.routes_events as routes_events
from app.deps import get_current_username
from app.firestore_client import get_db as real_get_db
from app.main import app
from tests.test_tree_endpoints import fake_db


def setup_module(module):
    # Override auth and db for all tests in this module
    module._orig_db = app.dependency_overrides.get(real_get_db)
    module._orig_user = app.dependency_overrides.get(get_current_username)
    app.dependency_overrides[real_get_db] = lambda: fake_db
    app.dependency_overrides[get_current_username] = lambda: "tester"
    # Monkeypatch direct imports used inside route modules
    module._orig_events_get_db = routes_events.get_db
    module._orig_auth_get_db = routes_auth.get_db
    routes_events.get_db = lambda: fake_db
    routes_auth.get_db = lambda: fake_db


def teardown_module(module):
    if module._orig_db is not None:
        app.dependency_overrides[real_get_db] = module._orig_db
    if module._orig_user is not None:
        app.dependency_overrides[get_current_username] = module._orig_user
    # restore monkeypatches
    routes_events.get_db = module._orig_events_get_db
    routes_auth.get_db = module._orig_auth_get_db


def setup_function(function):
    # Reset fake DB state before each test
    fake_db._store.clear()
    fake_db._store.update(
        {
            "members": {},
            "relations": {},
            "member_keys": {},
            "invites": {},
            "users": {},
        }
    )


def test_get_all_year_events_utility():
    """Test the get_all_year_events utility function."""
    # Create test members data
    members = [
        {
            "id": "member1",
            "first_name": "John",
            "last_name": "Doe",
            "dob": "1990-01-15",
            "dob_ts": 631843200,
            "is_deceased": False,
        },
        {
            "id": "member2",
            "first_name": "Jane",
            "last_name": "Smith",
            "dob": "1985-06-30",
            "dob_ts": 489024000,
            "is_deceased": False,
        },
    ]

    # Test function directly
    from app.routes_events import get_all_year_events

    upcoming, past = get_all_year_events(members)

    # Should return events (upcoming and past lists)
    assert isinstance(upcoming, list)
    assert isinstance(past, list)


def test_events_endpoint_no_members():
    """Test events endpoint when no members exist."""
    client = TestClient(app)

    response = client.get("/events/")
    assert response.status_code == 200

    data = response.json()
    assert "upcoming_events" in data
    assert "past_events" in data
    assert data["upcoming_events"] == []
    assert data["past_events"] == []


def test_events_endpoint_with_members():
    """Test events endpoint with sample members."""
    client = TestClient(app)

    # Add some test members to fake DB
    fake_db._store["members"]["member1"] = {
        "id": "member1",
        "first_name": "John",
        "last_name": "Doe",
        "dob": "1990-01-15",
        "dob_ts": 631843200,
        "is_deceased": False,
        "created_by": "tester",
    }

    response = client.get("/events/")
    assert response.status_code == 200

    data = response.json()
    assert "upcoming_events" in data
    assert "past_events" in data


def test_notification_settings_endpoint():
    """Test the notification settings update endpoint."""
    client = TestClient(app)

    # Test updating settings
    new_settings = {
        "enabled": True,
        "user_id": "tester",  # Match the mocked current user
    }

    response = client.post("/events/notifications/settings", json=new_settings)
    assert response.status_code == 200

    data = response.json()
    assert "ok" in data
    assert data["ok"] is True
    assert "enabled" in data


def test_notification_settings_update():
    """Test updating notification settings with false."""
    client = TestClient(app)

    # Test updating settings to disabled
    new_settings = {
        "enabled": False,
        "user_id": "tester",  # Match the mocked current user
    }

    response = client.post("/events/notifications/settings", json=new_settings)
    assert response.status_code == 200

    data = response.json()
    assert data["ok"] is True
    assert data["enabled"] is False
