#!/usr/bin/env python3
"""Migration script to move existing data into family spaces.

Prerequisites:
1. Firestore database must be set up in Google Cloud Console
2. GOOGLE_APPLICATION_CREDENTIALS must be set to service account key
3. Backend must have been running and have existing data

Usage:
    python migrate_to_spaces.py
"""

import os
import sys


def migrate_existing_data_to_demo():
    """Migrate all existing data to the demo space."""

    try:
        from google.cloud import firestore
    except ImportError:
        print("❌ Error: google-cloud-firestore package not installed")
        print("   Run: pip install google-cloud-firestore")
        return False

    # Check for credentials
    if not os.environ.get("GOOGLE_APPLICATION_CREDENTIALS"):
        print("❌ Error: GOOGLE_APPLICATION_CREDENTIALS environment variable not set")
        print("   Set it to the path of your service account key file")
        return False

    # Initialize Firestore
    print("🔄 Initializing Firestore connection...")
    try:
        # Use the family-tree database instead of default
        db = firestore.Client(database="family-tree")
    except Exception as e:
        print(f"❌ Error connecting to Firestore: {e}")
        print("   Make sure your database is set up in Google Cloud Console")
        return False

    print("🔄 Starting migration of existing data to demo space...")

    # 1. Ensure demo space exists
    print("📁 Ensuring demo space exists...")
    demo_space_ref = db.collection("family_spaces").document("demo")
    try:
        demo_doc = demo_space_ref.get()
        if not demo_doc.exists:
            demo_space_ref.set(
                {
                    "name": "Demo Family",
                    "description": "Default demo space for existing data",
                    "created_at": firestore.SERVER_TIMESTAMP,
                    "created_by": "system",
                }
            )
            print("✅ Created demo space")
        else:
            print("✅ Demo space already exists")
    except Exception as e:
        print(f"❌ Error creating demo space: {e}")
        return False

    # 2. Migrate members without space_id
    print("👥 Migrating members to demo space...")
    members_ref = db.collection("members")
    migrated_members = 0

    try:
        for doc in members_ref.stream():
            data = doc.to_dict()
            if not data.get("space_id"):
                # Add space_id to existing member
                doc.reference.update({"space_id": "demo"})
                migrated_members += 1
        print(f"✅ Migrated {migrated_members} members to demo space")
    except Exception as e:
        print(f"❌ Error migrating members: {e}")
        return False

    # 3. Migrate relations without space_id
    print("🔗 Migrating relations to demo space...")
    relations_ref = db.collection("relations")
    migrated_relations = 0

    try:
        for doc in relations_ref.stream():
            data = doc.to_dict()
            if not data.get("space_id"):
                # Add space_id to existing relation
                doc.reference.update({"space_id": "demo"})
                migrated_relations += 1
        print(f"✅ Migrated {migrated_relations} relations to demo space")
    except Exception as e:
        print(f"❌ Error migrating relations: {e}")
        return False

    # 4. Migrate users without current_space
    print("👤 Migrating users to demo space...")
    users_ref = db.collection("users")
    migrated_users = 0

    try:
        for doc in users_ref.stream():
            data = doc.to_dict()
            if not data.get("current_space"):
                # Set current_space to demo for existing users
                doc.reference.update({"current_space": "demo"})
                migrated_users += 1
        print(f"✅ Migrated {migrated_users} users to demo space")
    except Exception as e:
        print(f"❌ Error migrating users: {e}")
        return False

    # 5. Migrate invites without space_id
    print("📧 Migrating invites to demo space...")
    invites_ref = db.collection("invites")
    migrated_invites = 0

    try:
        for doc in invites_ref.stream():
            data = doc.to_dict()
            if not data.get("space_id"):
                # Add space_id to existing invite
                doc.reference.update({"space_id": "demo"})
                migrated_invites += 1
        print(f"✅ Migrated {migrated_invites} invites to demo space")
    except Exception as e:
        print(f"❌ Error migrating invites: {e}")
        return False

    # 6. Migrate event notifications
    print("🔔 Migrating event notifications...")
    event_notifications_ref = db.collection("event_notifications")
    migrated_notifications = 0

    try:
        # Create new space-scoped notifications for existing ones
        for doc in event_notifications_ref.stream():
            user_id = doc.id
            data = doc.to_dict()

            # Skip if this is already a space-scoped notification (contains underscore)
            if "_" in user_id:
                continue

            # Check if there's already a space-scoped notification
            space_doc_id = f"{user_id}_demo"
            space_notification_ref = event_notifications_ref.document(space_doc_id)

            if not space_notification_ref.get().exists:
                # Create space-scoped notification
                space_notification_ref.set(
                    {
                        "enabled": data.get("enabled", False),
                        "user_id": user_id,
                        "space_id": "demo",
                        "updated_at": firestore.SERVER_TIMESTAMP,
                    }
                )
                migrated_notifications += 1

        print(f"✅ Migrated {migrated_notifications} event notifications to demo space")
    except Exception as e:
        print(f"❌ Error migrating event notifications: {e}")
        return False

    print("🎉 Migration completed successfully!")
    print("📊 Summary:")
    print(f"   - {migrated_members} members migrated")
    print(f"   - {migrated_relations} relations migrated")
    print(f"   - {migrated_users} users migrated")
    print(f"   - {migrated_invites} invites migrated")
    print(f"   - {migrated_notifications} event notifications migrated")

    return True


if __name__ == "__main__":
    success = migrate_existing_data_to_demo()
    sys.exit(0 if success else 1)
