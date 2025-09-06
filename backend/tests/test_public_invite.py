#!/usr/bin/env python3
"""
Simple test script to verify the public invite endpoint works
"""

import requests

# Test configuration
API_BASE = "http://localhost:8080"
TEST_CODE = "test-invite-123"
TEST_EMAIL = "test@example.com"


def test_public_invite_endpoint():
    """Test the public invite email endpoint"""
    url = f"{API_BASE}/auth/public/invites/{TEST_CODE}/email"
    payload = {"email": TEST_EMAIL}

    try:
        response = requests.post(url, json=payload)
        print(f"Response status: {response.status_code}")
        print(f"Response body: {response.text}")

        if response.status_code == 404:
            print("✅ Expected 404 - invite code doesn't exist (this is normal for test)")
        elif response.status_code == 200:
            print("✅ Success - email sent")
        else:
            print(f"❌ Unexpected status code: {response.status_code}")

    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to API - is the server running?")
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    print("Testing public invite endpoint...")
    test_public_invite_endpoint()
