#!/usr/bin/env python3
"""
Initialize Firestore collections with proper structure.
This script creates the necessary collections that the family-tree app needs.
"""

import os
import sys

# Add the parent directory to the path so we can import from app
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.firestore_client import get_db


def initialize_collections():
    """Initialize all required Firestore collections."""
    try:
        db = get_db()
        print("🔄 Initializing Firestore collections...")

        # Collection 1: users
        # Create with a placeholder document (will be removed after first real user)
        users_ref = db.collection("users")
        users_ref.document("_placeholder").set(
            {
                "email": "placeholder@example.com",
                "created_at": "2025-01-01T00:00:00Z",
                "is_placeholder": True,
            }
        )
        print("✅ Created 'users' collection")

        # Collection 2: members
        # Create with a placeholder document
        members_ref = db.collection("members")
        members_ref.document("_placeholder").set(
            {
                "name": "Placeholder Member",
                "user_id": "_placeholder",
                "created_at": "2025-01-01T00:00:00Z",
                "is_placeholder": True,
            }
        )
        print("✅ Created 'members' collection")

        # Collection 3: relations
        # Create with a placeholder document
        relations_ref = db.collection("relations")
        relations_ref.document("_placeholder").set(
            {
                "parent_id": "_placeholder",
                "child_id": "_placeholder",
                "user_id": "_placeholder",
                "created_at": "2025-01-01T00:00:00Z",
                "is_placeholder": True,
            }
        )
        print("✅ Created 'relations' collection")

        # Collection 4: member_keys
        # For tracking deleted members
        member_keys_ref = db.collection("member_keys")
        member_keys_ref.document("_placeholder").set(
            {
                "original_id": "_placeholder",
                "user_id": "_placeholder",
                "deleted_at": "2025-01-01T00:00:00Z",
                "is_placeholder": True,
            }
        )
        print("✅ Created 'member_keys' collection")

        # Collection 5: tree_versions
        # For saving tree snapshots
        tree_versions_ref = db.collection("tree_versions")
        tree_versions_ref.document("_placeholder").set(
            {
                "user_id": "_placeholder",
                "members": [],
                "relations": [],
                "version": 0,
                "created_at": "2025-01-01T00:00:00Z",
                "is_placeholder": True,
            }
        )
        print("✅ Created 'tree_versions' collection")

        # Collection 6: tree_state
        # For tracking active version per user
        tree_state_ref = db.collection("tree_state")
        tree_state_ref.document("_placeholder").set(
            {
                "user_id": "_placeholder",
                "active_version": 0,
                "updated_at": "2025-01-01T00:00:00Z",
                "is_placeholder": True,
            }
        )
        print("✅ Created 'tree_state' collection")

        # Collection 7: invites
        # For user invitations (if used)
        invites_ref = db.collection("invites")
        invites_ref.document("_placeholder").set(
            {
                "email": "placeholder@example.com",
                "invited_by": "_placeholder",
                "created_at": "2025-01-01T00:00:00Z",
                "is_placeholder": True,
            }
        )
        print("✅ Created 'invites' collection")

        print("\n🎉 All collections initialized successfully!")
        print(
            "\nNote: Placeholder documents will be automatically cleaned up when real data is added."
        )
        print("You can now start using your family tree app with a fresh database.")

    except Exception as e:
        print(f"❌ Error initializing collections: {e}")
        return False

    return True


def cleanup_placeholders():
    """Optional: Clean up placeholder documents."""
    try:
        db = get_db()
        print("\n🔄 Cleaning up placeholder documents...")

        collections = [
            "users",
            "members",
            "relations",
            "member_keys",
            "tree_versions",
            "tree_state",
            "invites",
        ]

        for collection_name in collections:
            try:
                db.collection(collection_name).document("_placeholder").delete()
                print(f"✅ Cleaned up placeholder in '{collection_name}'")
            except Exception as e:
                print(f"⚠️  Could not clean up placeholder in '{collection_name}': {e}")

        print("\n🎉 Placeholder cleanup completed!")

    except Exception as e:
        print(f"❌ Error during cleanup: {e}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Initialize Firestore collections")
    parser.add_argument(
        "--cleanup", action="store_true", help="Clean up placeholder documents after initialization"
    )

    args = parser.parse_args()

    # Run the initialization
    success = initialize_collections()

    if success and args.cleanup:
        cleanup_placeholders()
    elif success:
        print(
            "\n💡 Tip: Run with --cleanup to remove placeholder documents after you add real data"
        )
