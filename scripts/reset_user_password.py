#!/usr/bin/env python3
"""
Reset a user's password hash in Firestore.

This script is useful after deploying the bcrypt fix to reset password hashes
for users who originally had passwords hashed with >72 bytes.

Usage:
    python scripts/reset_user_password.py <username> <new_password>

Example:
    python scripts/reset_user_password.py john.doe@example.com NewSecurePass123
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from app.auth_utils import hash_password
from app.firestore_client import get_db


def reset_user_password(username: str, new_password: str):
    """Reset a user's password in Firestore."""

    print(f"🔐 Resetting password for user: {username}")

    # Get Firestore client
    db = get_db()

    # Check if user exists
    user_ref = db.collection("users").document(username)
    user = user_ref.get()

    if not user.exists:
        print(f"❌ Error: User '{username}' not found")
        return False

    print("✅ User found")

    # Hash the new password (with truncation fix)
    print("🔒 Hashing new password...")
    new_hash = hash_password(new_password)

    # Update the password hash
    user_ref.update({"password_hash": new_hash})

    print("✅ Password reset successfully!")
    print(f"   User '{username}' can now log in with the new password")
    return True


def main():
    if len(sys.argv) != 3:
        print("❌ Error: Invalid arguments\n")
        print(f"Usage: {sys.argv[0]} <username> <new_password>")
        print(f"Example: {sys.argv[0]} john.doe@example.com NewSecurePass123")
        sys.exit(1)

    username = sys.argv[1]
    new_password = sys.argv[2]

    # Validate password length
    if len(new_password) < 8:
        print("❌ Error: Password must be at least 8 characters long")
        sys.exit(1)

    success = reset_user_password(username, new_password)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
