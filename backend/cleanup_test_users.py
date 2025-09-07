#!/usr/bin/env python3
"""
Script to remove test user accounts from the database.
This script removes specific test users that were created during development/testing.
"""

import os

from app.firestore_client import get_db


def main():
    """Remove specified test user accounts from the database."""

    # List of usernames to remove
    users_to_remove = [
        "r39132_1",
        "r39132_2",  # Note: user had "@" in original list but that's likely a typo
        "r39132_2@",  # Adding the version with @ as specified
        "r39132_3",
        "r39132_4",
        "r39132_5",
        "sanand_1",
        "sanand_4",
        "testuser",
        "testuser123",
        "test_user_123",
    ]

    print("=== CLEANUP TEST USERS SCRIPT ===")
    print(f"Database: {os.environ.get('FIRESTORE_DATABASE', '(default)')}")
    print(f"Users to remove: {users_to_remove}")
    print()

    db = get_db()

    removed_count = 0
    not_found_count = 0

    for username in users_to_remove:
        print(f"Checking user: {username}")

        # Check if user exists
        user_ref = db.collection("users").document(username)
        user_doc = user_ref.get()

        if user_doc.exists:
            user_data = user_doc.to_dict() or {}
            print(f"  ✓ Found user {username}")
            print(f"    Email: {user_data.get('email', 'N/A')}")
            print(f"    Created: {user_data.get('created_at', 'N/A')}")
            print(f"    Current space: {user_data.get('current_space', 'N/A')}")

            # Remove all related data first

            # 1. Remove members created by this user
            members_query = db.collection("members").where("created_by", "==", username)
            members = list(members_query.stream())
            print(f"    Removing {len(members)} members created by {username}")
            for member in members:
                member.reference.delete()

            # 2. Remove relations created by this user
            relations_query = db.collection("relations").where("created_by", "==", username)
            relations = list(relations_query.stream())
            print(f"    Removing {len(relations)} relations created by {username}")
            for relation in relations:
                relation.reference.delete()

            # 3. Remove invites created by this user
            invites_query = db.collection("invites").where("created_by", "==", username)
            invites = list(invites_query.stream())
            print(f"    Removing {len(invites)} invites created by {username}")
            for invite in invites:
                invite.reference.delete()

            # 4. Remove invites used by this user
            used_invites_query = db.collection("invites").where("used_by", "==", username)
            used_invites = list(used_invites_query.stream())
            print(f"    Removing {len(used_invites)} invites used by {username}")
            for invite in used_invites:
                invite.reference.delete()

            # 5. Remove event notifications for this user
            notifications_query = db.collection("event_notifications").where(
                "user_id", "==", username
            )
            notifications = list(notifications_query.stream())
            print(f"    Removing {len(notifications)} event notifications for {username}")
            for notification in notifications:
                notification.reference.delete()

            # 6. Finally, remove the user account
            user_ref.delete()
            print(f"    ✅ Removed user account: {username}")
            removed_count += 1

        else:
            print(f"  ⚠️  User {username} not found in database")
            not_found_count += 1

        print()

    print("=== CLEANUP SUMMARY ===")
    print(f"Users removed: {removed_count}")
    print(f"Users not found: {not_found_count}")
    print(f"Total processed: {len(users_to_remove)}")

    if removed_count > 0:
        print(f"✅ Successfully cleaned up {removed_count} test user accounts")
    else:
        print("ℹ️  No users were removed (all users already absent)")


if __name__ == "__main__":
    main()
