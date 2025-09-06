#!/usr/bin/env python3
"""
Test script to verify the events API is working.
Run this after starting the backend to test the events functionality.
"""

import sys
from datetime import datetime, timedelta

import requests

# Configuration
API_BASE = "http://localhost:8080"
TEST_USERNAME = "test_user"
TEST_PASSWORD = "test_password"
TEST_EMAIL = "test@example.com"


def register_and_login():
    """Register a test user and login to get a token"""
    try:
        # Try to login first
        login_data = {"username": TEST_USERNAME, "password": TEST_PASSWORD}
        response = requests.post(f"{API_BASE}/auth/login", json=login_data)
        if response.status_code == 200:
            return response.json()["access_token"]
        print(f"Login failed: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"Login exception: {e}")

    # If login fails, try to register
    try:
        register_data = {
            "invite_code": "test-invite",
            "username": TEST_USERNAME,
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD,
        }
        response = requests.post(f"{API_BASE}/auth/register", json=register_data)
        print(f"Register response: {response.status_code} - {response.text}")

        if response.status_code == 200:
            # Now login
            login_data = {"username": TEST_USERNAME, "password": TEST_PASSWORD}
            response = requests.post(f"{API_BASE}/auth/login", json=login_data)
            if response.status_code == 200:
                return response.json()["access_token"]
            print(f"Login after register failed: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"Register exception: {e}")

    return None


def add_test_member(token, name_parts, dob, is_deceased=False):
    """Add a test member with the given details"""
    member_data = {
        "first_name": name_parts[0],
        "last_name": name_parts[1],
        "dob": dob,
        "is_deceased": is_deceased,
    }

    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post(f"{API_BASE}/tree/members", json=member_data, headers=headers)

    if response.status_code == 201:
        print(f"Added member: {name_parts[0]} {name_parts[1]} (DOB: {dob})")
        return response.json()["id"]
    else:
        print(f"Failed to add member {name_parts[0]} {name_parts[1]}: {response.text}")
        return None


def test_events(token):
    """Test the events API endpoints"""
    headers = {"Authorization": f"Bearer {token}"}

    # Test getting events
    print("\n=== Testing Events API ===")
    response = requests.get(f"{API_BASE}/events/", headers=headers)

    if response.status_code == 200:
        data = response.json()
        print("✅ Events API working!")
        print(f"📅 Found {len(data['upcoming_events'])} upcoming events")
        print(f"🔔 Notifications enabled: {data['notification_enabled']}")

        # Display first few events
        for i, event in enumerate(data["upcoming_events"][:3]):
            event_type = (
                "🎂 Birthday" if event["event_type"] == "birthday" else "🕊️ Death Anniversary"
            )
            print(
                f"   {i + 1}. {event['member_name']} - {event_type} on {event['event_date']} (age {event['age_on_date']})"
            )
    else:
        print(f"❌ Events API failed: {response.status_code} - {response.text}")
        return False

    # Test notification settings
    print("\n=== Testing Notification Settings ===")

    # Enable notifications
    settings_data = {"enabled": True, "user_id": ""}
    response = requests.post(
        f"{API_BASE}/events/notifications/settings", json=settings_data, headers=headers
    )

    if response.status_code == 200:
        print("✅ Successfully enabled notifications")
    else:
        print(f"❌ Failed to update notification settings: {response.text}")

    # Check if settings were updated
    response = requests.get(f"{API_BASE}/events/", headers=headers)
    if response.status_code == 200:
        data = response.json()
        print(f"🔔 Notifications now enabled: {data['notification_enabled']}")

    return True


def main():
    print("🌳 Family Tree Events API Test")
    print("=" * 40)

    # Get authentication token
    token = register_and_login()
    if not token:
        print("❌ Failed to authenticate")
        sys.exit(1)

    print("✅ Authentication successful")

    # Add some test members with upcoming birthdays
    today = datetime.now()

    # Member with birthday next week
    next_week = today + timedelta(days=7)
    birthday_next_week = f"{next_week.year}-{next_week.month:02d}-{next_week.day:02d}"

    # Member with birthday next month
    next_month = today + timedelta(days=30)
    birthday_next_month = f"{next_month.year}-{next_month.month:02d}-{next_month.day:02d}"

    # Member born 25 years ago (birthday this year)
    birth_25_years_ago = today - timedelta(days=25 * 365)
    birthday_25 = (
        f"{birth_25_years_ago.year}-{birth_25_years_ago.month:02d}-{birth_25_years_ago.day:02d}"
    )

    print("\n=== Adding Test Members ===")
    add_test_member(token, ["Alice", "Johnson"], birthday_next_week)
    add_test_member(token, ["Bob", "Smith"], birthday_next_month)
    add_test_member(token, ["Charlie", "Brown"], birthday_25)
    add_test_member(token, ["Diana", "Wilson"], "1950-01-15", is_deceased=True)

    # Test the events API
    success = test_events(token)

    if success:
        print("\n🎉 Events API test completed successfully!")
        print("👀 You can now view the events page at http://localhost:3000/events")
        print("   (Make sure to login with the test user credentials)")
    else:
        print("\n❌ Events API test failed")
        sys.exit(1)


if __name__ == "__main__":
    main()
