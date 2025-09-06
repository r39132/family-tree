#!/usr/bin/env python3
"""
Quick test to validate the improved error messages for redeemed invites
"""

import requests
import json

BASE_URL = "http://localhost:8000"


def test_redeemed_invite_error():
    """Test that redeemed invites show proper error message"""
    print("🧪 Testing redeemed invite error message...")

    # Use the invite code from the screenshot that was already redeemed
    invite_code = "fc085461-bc69-4cd9-9ebc-0a22f1405787"

    # Test the validate endpoint
    response = requests.get(f"{BASE_URL}/auth/invites/{invite_code}/validate")

    print(f"Validation response: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Response data: {json.dumps(data, indent=2)}")

        if not data.get("valid") and data.get("error") == "redeemed":
            print("✅ Validation endpoint returns correct error type")
            if "This invite code has already been redeemed" in data.get("message", ""):
                print("✅ Error message is correct and improved!")
            else:
                print(f"❌ Error message needs improvement: {data.get('message')}")
        else:
            print("❌ Validation endpoint not returning expected redeemed error")
    else:
        print(f"❌ Validation endpoint failed: {response.text}")


if __name__ == "__main__":
    test_redeemed_invite_error()
