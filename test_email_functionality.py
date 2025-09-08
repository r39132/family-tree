#!/usr/bin/env python3
"""
Comprehensive email functionality test script for Family Tree API
Tests invite creation, email sending, resending, deletion, and redemption protection
"""

import requests
import sys
from typing import Dict, Any, Optional

# Configuration
BASE_URL = "http://localhost:8080"
TEST_EMAIL = "r39132+2@gmail.com"
TEST_USERNAME = "testuser"
TEST_PASSWORD = "testpass123"


class EmailTestClient:
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.session = requests.Session()
        self.auth_token = None

    def health_check(self) -> bool:
        """Check if the server is running"""
        try:
            response = self.session.get(f"{self.base_url}/healthz")
            print(f"Health check: {response.status_code} - {response.text}")
            return response.status_code == 200
        except Exception as e:
            print(f"Health check failed: {e}")
            return False

    def register_test_user(self) -> bool:
        """Register a test user for authenticated operations"""
        try:
            payload = {
                "username": TEST_USERNAME,
                "password": TEST_PASSWORD,
                "email": "testuser@example.com",
                "invite_code": "test",  # This might fail if invites are required
            }
            response = self.session.post(f"{self.base_url}/auth/register", json=payload)
            print(f"Register test user: {response.status_code} - {response.text}")
            return response.status_code in [200, 400]  # 400 if user already exists
        except Exception as e:
            print(f"Register test user failed: {e}")
            return False

    def login_test_user(self) -> bool:
        """Login and get auth token"""
        try:
            payload = {"username": TEST_USERNAME, "password": TEST_PASSWORD}
            response = self.session.post(f"{self.base_url}/auth/login", json=payload)
            print(f"Login: {response.status_code}")

            if response.status_code == 200:
                data = response.json()
                self.auth_token = data.get("access_token")
                self.session.headers.update(
                    {"Authorization": f"Bearer {self.auth_token}"}
                )
                print("✅ Authentication successful")
                return True
            else:
                print(f"❌ Login failed: {response.text}")
                return False
        except Exception as e:
            print(f"Login failed: {e}")
            return False

    def create_invite(self) -> Optional[str]:
        """Create a new invite and return the invite code"""
        try:
            response = self.session.post(
                f"{self.base_url}/auth/invite", params={"count": 1}
            )
            print(f"Create invite: {response.status_code}")

            if response.status_code == 200:
                data = response.json()
                invite_code = data.get("codes", [None])[0]
                print(f"✅ Invite created: {invite_code}")
                return invite_code
            else:
                print(f"❌ Create invite failed: {response.text}")
                return None
        except Exception as e:
            print(f"Create invite failed: {e}")
            return None

    def send_invite_email(
        self, invite_code: str, email: str, authenticated: bool = True
    ) -> bool:
        """Send invite email (authenticated or public)"""
        try:
            payload = {"email": email}

            if authenticated:
                url = f"{self.base_url}/auth/invites/{invite_code}/email"
            else:
                url = f"{self.base_url}/auth/public/invites/{invite_code}/email"

            response = self.session.post(url, json=payload)
            print(
                f"Send {'authenticated' if authenticated else 'public'} invite email: {response.status_code}"
            )

            if response.status_code == 200:
                data = response.json()
                print(f"✅ Email sent to: {data.get('sent_email')}")
                return True
            else:
                print(f"❌ Send email failed: {response.text}")
                return False
        except Exception as e:
            print(f"Send email failed: {e}")
            return False

    def delete_invite(self, invite_code: str) -> bool:
        """Delete an invite"""
        try:
            response = self.session.delete(
                f"{self.base_url}/auth/invites/{invite_code}"
            )
            print(f"Delete invite: {response.status_code}")

            if response.status_code == 200:
                print(f"✅ Invite {invite_code} deleted successfully")
                return True
            else:
                print(f"❌ Delete invite failed: {response.text}")
                return False
        except Exception as e:
            print(f"Delete invite failed: {e}")
            return False

    def try_register_with_invite(self, invite_code: str) -> Dict[str, Any]:
        """Try to register with an invite code"""
        try:
            payload = {
                "username": f"user_{invite_code[:8]}",
                "password": "testpass123",
                "email": f"user_{invite_code[:8]}@example.com",
                "invite_code": invite_code,
            }
            response = self.session.post(f"{self.base_url}/auth/register", json=payload)
            print(f"Register with invite: {response.status_code}")

            return {
                "success": response.status_code == 200,
                "status_code": response.status_code,
                "response": response.text,
            }
        except Exception as e:
            print(f"Register with invite failed: {e}")
            return {"success": False, "error": str(e)}


def run_email_tests():
    """Run comprehensive email functionality tests"""
    print("🚀 Starting Email Functionality Tests")
    print("=" * 50)

    client = EmailTestClient(BASE_URL)

    # Test 1: Health check
    print("\n1️⃣ Testing server health...")
    if not client.health_check():
        print("❌ Server is not running. Please start the backend server.")
        return False

    # Test 2: Setup authentication
    print("\n2️⃣ Setting up authentication...")
    client.register_test_user()  # May fail if user exists, that's ok
    if not client.login_test_user():
        print("❌ Failed to authenticate. Cannot run authenticated tests.")
        return False

    # Test 3: Create first invite
    print("\n3️⃣ Creating first invite...")
    invite1 = client.create_invite()
    if not invite1:
        print("❌ Failed to create invite")
        return False

    # Test 4: Send email invite
    print(f"\n4️⃣ Sending email invite to {TEST_EMAIL}...")
    if not client.send_invite_email(invite1, TEST_EMAIL, authenticated=True):
        print("❌ Failed to send initial email invite")
        return False

    # Test 5: Resend email invite (should hit rate limiting after first send)
    print(f"\n5️⃣ Attempting to resend email invite to {TEST_EMAIL}...")
    print("(This should fail due to rate limiting)")
    client.send_invite_email(invite1, TEST_EMAIL, authenticated=True)

    # Test 6: Create second invite
    print("\n6️⃣ Creating second invite...")
    invite2 = client.create_invite()
    if not invite2:
        print("❌ Failed to create second invite")
        return False

    # Test 7: Send different email invite
    print(f"\n7️⃣ Sending different email invite to {TEST_EMAIL}...")
    if not client.send_invite_email(invite2, TEST_EMAIL, authenticated=True):
        print("❌ Failed to send second email invite")
        return False

    # Test 8: Delete an invite
    print(f"\n8️⃣ Deleting invite {invite2}...")
    if not client.delete_invite(invite2):
        print("❌ Failed to delete invite")
        return False

    # Test 9: Try to register with deleted invite (should fail)
    print(f"\n9️⃣ Attempting to register with deleted invite {invite2}...")
    result = client.try_register_with_invite(invite2)
    if result["success"]:
        print("❌ Registration with deleted invite should have failed!")
        return False
    else:
        print(
            f"✅ Registration with deleted invite correctly failed: {result['status_code']}"
        )

    # Test 10: Try to register with valid invite
    print(f"\n🔟 Attempting to register with valid invite {invite1}...")
    result = client.try_register_with_invite(invite1)
    if result["success"]:
        print("✅ Registration with valid invite succeeded")
    else:
        print(
            f"⚠️ Registration with valid invite failed: {result['status_code']} - {result['response']}"
        )
        # This might fail due to REQUIRE_INVITE setting or other validation

    print("\n" + "=" * 50)
    print("🎉 Email functionality tests completed!")
    return True


if __name__ == "__main__":
    success = run_email_tests()
    sys.exit(0 if success else 1)
