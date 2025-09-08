"""Tests for individual event notification functionality."""

from datetime import datetime, timedelta
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

import app.routes_auth as routes_auth
import app.routes_events as routes_events
from app.deps import get_current_username
from app.firestore_client import get_db as real_get_db
from app.main import app
from app.utils.time import utc_now
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
            "event_notifications": {},
            "event_notification_logs": {},
        }
    )


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def setup_test_data():
    """Setup test users, members, and notification settings."""
    # Create test user with email
    fake_db.collection("users").document("tester").set(
        {"email": "tester@example.com", "current_space": "test-space", "username": "tester"}
    )

    # Another user for testing
    fake_db.collection("users").document("user2").set(
        {"email": "user2@example.com", "current_space": "test-space", "username": "user2"}
    )

    # Create test members with upcoming events
    today = utc_now().date()
    tomorrow = today + timedelta(days=1)

    # Member with birthday tomorrow
    fake_db.collection("members").document("member1").set(
        {
            "first_name": "John",
            "last_name": "Doe",
            "space_id": "test-space",
            "dob": f"1990-{tomorrow.month:02d}-{tomorrow.day:02d}",
            "created_by": "tester",
        }
    )

    # Member with death anniversary tomorrow
    fake_db.collection("members").document("member2").set(
        {
            "first_name": "Jane",
            "last_name": "Smith",
            "space_id": "test-space",
            "dob": "1950-01-01",
            "date_of_death": f"2020-{tomorrow.month:02d}-{tomorrow.day:02d}",
            "is_deceased": True,
            "created_by": "tester",
        }
    )

    # Member with no upcoming events
    fake_db.collection("members").document("member3").set(
        {
            "first_name": "Bob",
            "last_name": "Wilson",
            "space_id": "test-space",
            "dob": "1985-12-25",  # Christmas, probably not tomorrow
            "created_by": "tester",
        }
    )

    # Enable notifications for both users
    fake_db.collection("event_notifications").document("tester_test-space").set(
        {"enabled": True, "user_id": "tester", "space_id": "test-space"}
    )

    fake_db.collection("event_notifications").document("user2_test-space").set(
        {"enabled": True, "user_id": "user2", "space_id": "test-space"}
    )


def test_send_individual_event_reminders(client, setup_test_data):
    """Test that individual emails are sent for each upcoming event."""
    sent_emails = []

    def mock_send_mail(to_email, subject, body):
        sent_emails.append({"to": to_email, "subject": subject, "body": body})

    with patch("app.routes_events.send_mail", side_effect=mock_send_mail):
        response = client.post("/events/notifications/send-reminders")

    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is True
    assert data["sent"] > 0  # Should have sent some emails

    # Should send individual emails to both users for both events
    # 2 users × 2 events = 4 emails
    assert len(sent_emails) == 4

    # Check that we get different subjects for different event types
    subjects = [email["subject"] for email in sent_emails]
    birthday_emails = [s for s in subjects if "Birthday" in s]
    remembrance_emails = [s for s in subjects if "Remembrance" in s]

    assert len(birthday_emails) == 2  # One for each user
    assert len(remembrance_emails) == 2  # One for each user

    # Verify individual email content
    birthday_email = next(email for email in sent_emails if "Birthday" in email["subject"])
    assert "John Doe" in birthday_email["subject"]
    assert "birthday is coming up" in birthday_email["body"]
    assert "Turning" in birthday_email["body"]

    remembrance_email = next(email for email in sent_emails if "Remembrance" in email["subject"])
    assert "Jane Smith" in remembrance_email["subject"]
    assert "remembrance day" in remembrance_email["body"]
    assert "years since they passed" in remembrance_email["body"]


def test_no_duplicate_notifications(client, setup_test_data):
    """Test that duplicate notifications are not sent for the same event."""
    sent_emails = []

    def mock_send_mail(to_email, subject, body):
        sent_emails.append({"to": to_email, "subject": subject, "body": body})

    with patch("app.routes_events.send_mail", side_effect=mock_send_mail):
        # Send notifications first time
        response1 = client.post("/events/notifications/send-reminders")
        assert response1.status_code == 200

        first_count = len(sent_emails)
        assert first_count > 0

        # Send notifications second time - should not send duplicates
        response2 = client.post("/events/notifications/send-reminders")
        assert response2.status_code == 200

        # No new emails should be sent
        assert len(sent_emails) == first_count

        data2 = response2.json()
        assert data2["sent"] == 0  # No new notifications sent


def test_notification_logs_are_created(client, setup_test_data):
    """Test that notification logs are properly created when emails are sent."""
    sent_emails = []

    def mock_send_mail(to_email, subject, body):
        sent_emails.append({"to": to_email, "subject": subject, "body": body})

    with patch("app.routes_events.send_mail", side_effect=mock_send_mail):
        response = client.post("/events/notifications/send-reminders")

    assert response.status_code == 200
    assert len(sent_emails) > 0

    # Check that notification logs were created
    logs_response = client.get("/events/notifications/logs")
    assert logs_response.status_code == 200

    logs_data = logs_response.json()
    assert "logs" in logs_data
    assert len(logs_data["logs"]) == len(sent_emails)

    # Verify log structure
    log = logs_data["logs"][0]
    assert "user_id" in log
    assert "space_id" in log
    assert "member_id" in log
    assert "event_type" in log
    assert "event_date" in log
    assert "notification_sent_at" in log
    assert log["space_id"] == "test-space"
    assert log["event_type"] in ["birthday", "death_anniversary"]


def test_no_notifications_when_disabled(client, setup_test_data):
    """Test that no notifications are sent when notifications are disabled."""
    # Disable notifications for all users
    fake_db.collection("event_notifications").document("tester_test-space").update(
        {"enabled": False}
    )
    fake_db.collection("event_notifications").document("user2_test-space").update(
        {"enabled": False}
    )

    sent_emails = []

    def mock_send_mail(to_email, subject, body):
        sent_emails.append({"to": to_email, "subject": subject, "body": body})

    with patch("app.routes_events.send_mail", side_effect=mock_send_mail):
        response = client.post("/events/notifications/send-reminders")

    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is True
    assert data["sent"] == 0
    assert len(sent_emails) == 0
    assert "No users have notifications enabled" in data["message"]


def test_email_failure_handling(client, setup_test_data):
    """Test that email failures are handled gracefully and don't stop other notifications."""
    sent_emails = []
    failed_emails = []

    def mock_send_mail(to_email, subject, body):
        if to_email == "tester@example.com":
            # Simulate failure for first user
            failed_emails.append(to_email)
            raise Exception("SMTP connection failed")
        else:
            # Success for second user
            sent_emails.append({"to": to_email, "subject": subject, "body": body})

    with patch("app.routes_events.send_mail", side_effect=mock_send_mail):
        response = client.post("/events/notifications/send-reminders")

    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is True

    # Should have attempted to send to both users but only succeeded for one
    assert len(failed_emails) > 0
    assert len(sent_emails) > 0  # Some emails should still be sent

    # Verify that notification logs are only created for successful sends
    logs_response = client.get("/events/notifications/logs")
    assert logs_response.status_code == 200
    logs_data = logs_response.json()

    # Only successful notifications should be logged
    assert len(logs_data["logs"]) == len(sent_emails)


def test_notification_logs_with_limit(client, setup_test_data):
    """Test that notification logs endpoint respects limit parameter."""
    sent_emails = []

    def mock_send_mail(to_email, subject, body):
        sent_emails.append({"to": to_email, "subject": subject, "body": body})

    with patch("app.routes_events.send_mail", side_effect=mock_send_mail):
        # Send notifications to create logs
        response = client.post("/events/notifications/send-reminders")
        assert response.status_code == 200

    # Test with different limits
    logs_response = client.get("/events/notifications/logs?limit=2")
    assert logs_response.status_code == 200
    logs_data = logs_response.json()

    # Should respect the limit (though might be less if total logs < limit)
    assert len(logs_data["logs"]) <= 2
    assert logs_data["space_id"] == "test-space"


def test_events_far_in_future_not_notified(client, setup_test_data):
    """Test that events more than 2 days away don't trigger notifications."""
    # Add a member with birthday 5 days from now (outside the 48-hour window)
    today = utc_now().date()
    future_date = today + timedelta(days=5)

    fake_db.collection("members").document("future_member").set(
        {
            "first_name": "Future",
            "last_name": "Person",
            "space_id": "test-space",
            "dob": f"1995-{future_date.month:02d}-{future_date.day:02d}",
            "created_by": "tester",
        }
    )

    sent_emails = []

    def mock_send_mail(to_email, subject, body):
        sent_emails.append({"to": to_email, "subject": subject, "body": body})

    with patch("app.routes_events.send_mail", side_effect=mock_send_mail):
        response = client.post("/events/notifications/send-reminders")

    assert response.status_code == 200

    # Check that no emails mention the future person
    future_mentions = [
        email
        for email in sent_emails
        if "Future Person" in email["subject"] or "Future Person" in email["body"]
    ]
    assert len(future_mentions) == 0


def test_recent_enabler_receives_notification(client, setup_test_data):
    """Test that users who recently enabled notifications receive emails even if events are imminent."""
    from datetime import timezone

    sent_emails = []

    def mock_send_mail(to_email, subject, body):
        sent_emails.append({"to": to_email, "subject": subject, "body": body})

    # First, send normal notifications
    with patch("app.routes_events.send_mail", side_effect=mock_send_mail):
        response = client.post("/events/notifications/send-reminders")
        assert response.status_code == 200
        initial_count = len(sent_emails)
        assert initial_count > 0

    # Clear emails
    sent_emails.clear()

    # Simulate a new user enabling notifications very recently (2 hours ago)
    recent_time = datetime.now(timezone.utc) - timedelta(hours=2)
    fake_db.collection("event_notifications").document("newuser_test-space").set(
        {"enabled": True, "user_id": "newuser", "space_id": "test-space", "updated_at": recent_time}
    )

    # Add the new user
    fake_db.collection("users").document("newuser").set(
        {"email": "newuser@example.com", "current_space": "test-space", "username": "newuser"}
    )

    # Run notifications again - the recent enabler should receive notifications
    with patch("app.routes_events.send_mail", side_effect=mock_send_mail):
        response = client.post("/events/notifications/send-reminders")
        assert response.status_code == 200

    # Check that the new user received notifications despite logs existing for other users
    new_user_emails = [email for email in sent_emails if email["to"] == "newuser@example.com"]
    assert len(new_user_emails) > 0, "Recent enabler should receive notifications"

    # Check that existing users didn't get duplicate notifications
    existing_user_emails = [
        email for email in sent_emails if email["to"] in ["tester@example.com", "user2@example.com"]
    ]
    assert len(existing_user_emails) == 0, "Existing users should not get duplicate notifications"


def test_user_without_email_skipped(client, setup_test_data):
    """Test that users without email addresses are skipped."""
    # Create a user without email
    fake_db.collection("users").document("no_email_user").set(
        {
            "username": "no_email_user",
            "current_space": "test-space",
            # No email field
        }
    )

    # Enable notifications for this user
    fake_db.collection("event_notifications").document("no_email_user_test-space").set(
        {"enabled": True, "user_id": "no_email_user", "space_id": "test-space"}
    )

    sent_emails = []

    def mock_send_mail(to_email, subject, body):
        sent_emails.append({"to": to_email, "subject": subject, "body": body})

    with patch("app.routes_events.send_mail", side_effect=mock_send_mail):
        response = client.post("/events/notifications/send-reminders")

    assert response.status_code == 200

    # Should still send emails to users with valid email addresses
    assert len(sent_emails) > 0

    # But no emails should be sent to empty/None addresses
    email_addresses = [email["to"] for email in sent_emails]
    assert all(addr and "@" in addr for addr in email_addresses)
