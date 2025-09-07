#!/usr/bin/env python3
"""Seed script to create family spaces and admin users.

Prerequisites:
1. Firestore database must be set up in Google Cloud Console
2. GOOGLE_APPLICATION_CREDENTIALS must be set to service account key
3. Backend dependencies must be installed

Usage:
    python seed_spaces.py
"""

import os
import sys


def seed_family_spaces():
    """Create family spaces and admin users."""

    try:
        from google.cloud import firestore

        # Import from the app to use the existing auth utilities
        sys.path.append("/Users/r39132/Projects/family-tree/backend")
        from app.auth_utils import hash_password
    except ImportError as e:
        print(f"❌ Error: Required package not installed: {e}")
        print("   Make sure all dependencies are installed")
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

    # Define the spaces to create
    spaces_to_create = [
        {
            "id": "demo",
            "name": "Demo Family",
            "description": "Default demo space for existing data",
        },
        {
            "id": "karunakaran",
            "name": "Karunakaran Family",
            "description": "Family space for the Karunakaran family tree",
        },
        {
            "id": "anand",
            "name": "Anand Family",
            "description": "Family space for the Anand family tree",
        },
        {
            "id": "kullatira",
            "name": "Kullatira Family",
            "description": "Family space for the Kullatira family tree",
        },
    ]

    print("🔄 Creating family spaces...")

    # Create family spaces
    for space in spaces_to_create:
        space_ref = db.collection("family_spaces").document(space["id"])
        space_doc = space_ref.get()

        if not space_doc.exists:
            space_ref.set(
                {
                    "name": space["name"],
                    "description": space["description"],
                    "created_at": firestore.SERVER_TIMESTAMP,
                    "created_by": "system",
                }
            )
            print(f"✅ Created space: {space['name']} ({space['id']})")
        else:
            print(f"✅ Space already exists: {space['name']} ({space['id']})")

    # Create sanand admin user for non-demo spaces
    print("🔄 Creating admin user sanand...")

    non_demo_spaces = ["karunakaran", "anand", "kullatira"]

    user_id = "sanand"
    user_ref = db.collection("users").document(user_id)
    user_doc = user_ref.get()

    if not user_doc.exists:
        # Create the user (only once)
        user_ref.set(
            {
                "email": "sanand@apache.org",
                "password_hash": hash_password("admin123"),  # Default password
                "created_at": firestore.SERVER_TIMESTAMP,
                "current_space": "karunakaran",  # Default to first space
                "is_admin": True,
            }
        )
        print(f"✅ Created admin user: {user_id} (sanand@apache.org)")
    else:
        # Update to ensure admin status
        user_ref.update(
            {
                "is_admin": True,
                "email": "sanand@apache.org",  # Ensure email is set
            }
        )
        print(f"✅ Updated admin user: {user_id}")

    # Create initial member for sanand in each non-demo space
    for space_id in non_demo_spaces:
        member_id = f"sanand_{space_id}"
        member_ref = db.collection("members").document(member_id)
        member_doc = member_ref.get()

        if not member_doc.exists:
            member_ref.set(
                {
                    "first_name": "Sanand",
                    "last_name": "Administrator",
                    "dob": "1980-01-01",
                    "created_by": user_id,
                    "space_id": space_id,
                    "created_at": firestore.SERVER_TIMESTAMP,
                }
            )
            print(f"✅ Created admin member in {space_id} space")

    print("🎉 Seeding completed successfully!")
    print()
    print("📋 Admin Login Details:")
    print("   Username: sanand")
    print("   Email: sanand@apache.org")
    print("   Password: admin123")
    print("   Spaces: karunakaran, anand, kullatira")
    print()
    print("⚠️  IMPORTANT: Change the admin password after first login!")

    return True


if __name__ == "__main__":
    success = seed_family_spaces()
    sys.exit(0 if success else 1)
