#!/usr/bin/env python3
"""
Create a user account for login testing.
"""

import os
import sys
from datetime import datetime

# Add the parent directory to the path so we can import from app
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.auth_utils import hash_password
from app.firestore_client import get_db


def create_user_account(username: str, email: str, password: str):
    """Create a user account with the specified credentials."""
    db = get_db()

    print(f"🔄 Creating user account: {username}")

    # Check if user already exists
    user_ref = db.collection("users").document(username)
    if user_ref.get().exists:
        print(f"⚠️  User '{username}' already exists. Updating password...")

    # Create/update user with proper authentication
    user_data = {
        "email": email,
        "password_hash": hash_password(password),
        "created_at": datetime.now().isoformat(),
        "invite_code_used": "admin_created",
    }

    user_ref.set(user_data)
    print(f"✅ Created/updated user: {username}")
    print(f"📧 Email: {email}")
    print(f"🔑 Password: {password}")

    # Initialize tree state for the user
    tree_state_data = {
        "user_id": username,
        "active_version": 0,  # No saved versions yet
        "updated_at": datetime.now().isoformat(),
    }

    db.collection("tree_state").document(username).set(tree_state_data)
    print("✅ Initialized tree state")

    return username


def transfer_dummy_data_to_user(from_user: str, to_user: str):
    """Transfer dummy data from test user to the new user."""
    db = get_db()

    print(f"🔄 Transferring data from {from_user} to {to_user}...")

    # Transfer members
    members_query = db.collection("members").where("user_id", "==", from_user)
    members = list(members_query.stream())

    if members:
        print(f"📋 Transferring {len(members)} members...")
        for member_doc in members:
            member_data = member_doc.to_dict()
            member_data["user_id"] = to_user
            # Create new document for the new user
            db.collection("members").document(member_doc.id).set(member_data)
        print(f"✅ Transferred {len(members)} members")

    # Transfer relations
    relations_query = db.collection("relations").where("user_id", "==", from_user)
    relations = list(relations_query.stream())

    if relations:
        print(f"🔗 Transferring {len(relations)} relations...")
        for relation_doc in relations:
            relation_data = relation_doc.to_dict()
            relation_data["user_id"] = to_user
            # Update existing document
            db.collection("relations").document(relation_doc.id).set(relation_data)
        print(f"✅ Transferred {len(relations)} relations")

    # Update tree state
    tree_state_data = {
        "user_id": to_user,
        "active_version": 0,
        "updated_at": datetime.now().isoformat(),
    }
    db.collection("tree_state").document(to_user).set(tree_state_data)
    print("✅ Updated tree state")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Create user accounts")
    parser.add_argument("--username", default="sanand", help="Username")
    parser.add_argument("--email", default="sanand@apache.org", help="Email")
    parser.add_argument("--password", default="pw", help="Password")
    parser.add_argument("--no-transfer", action="store_true", help="Don't transfer dummy data")

    args = parser.parse_args()

    # Create the user account
    create_user_account(args.username, args.email, args.password)

    if not args.no_transfer:
        # Transfer dummy data from test user to the new user
        transfer_dummy_data_to_user("test_user_123", args.username)

    print("\n🎉 User account ready!")
    print(f"👤 Username: {args.username}")
    print(f"📧 Email: {args.email}")
    print(f"🔑 Password: {args.password}")
    print("\n💡 You can now log in to the family tree app with these credentials.")
