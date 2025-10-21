#!/usr/bin/env python3
"""
Migrate existing profile pictures to space-organized structure.

Old structure: profile-pictures/{member_id}/{uuid}.jpg
New structure: {space_id}/profile-pictures/{member_id}/{uuid}.jpg

This script:
1. Lists all existing profile pictures in GCS
2. For each picture, looks up the member's space_id
3. Copies the image to the new location
4. Updates the member's profile_picture_url
5. Optionally deletes the old image
"""

import os
import sys
from datetime import timedelta

# Add parent directory to path to import app modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from dotenv import load_dotenv  # noqa: E402
from google.cloud import firestore, storage  # noqa: E402

from app.config import settings  # noqa: E402

# Load environment variables from .env file
env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
load_dotenv(env_path)


def get_member_space(db, member_id: str) -> str | None:
    """Get the space_id for a member."""
    member_doc = db.collection("members").document(member_id).get()
    if not member_doc.exists:
        print(f"  ⚠️  Member {member_id} not found in Firestore")
        return None

    data = member_doc.to_dict()
    space_id = data.get("space_id", "demo")
    name = f"{data.get('first_name', '')} {data.get('last_name', '')}"
    print(f"  📋 Member: {name} (space: {space_id})")
    return space_id


def migrate_profile_pictures(dry_run=True):
    """Migrate profile pictures to space-organized structure."""
    if not settings.gcs_bucket_name:
        print("❌ GCS_BUCKET_NAME not configured")
        return

    print(f"🪣 Bucket: {settings.gcs_bucket_name}")
    print(f"{'🔍 DRY RUN MODE' if dry_run else '✅ LIVE MODE'}\n")

    # Initialize clients
    storage_client = storage.Client()
    # Use the configured Firestore database name
    db = firestore.Client(database=os.environ.get("FIRESTORE_DATABASE", "(default)"))
    bucket = storage_client.bucket(settings.gcs_bucket_name)

    # List all blobs in the old structure
    prefix = "profile-pictures/"
    blobs = list(bucket.list_blobs(prefix=prefix))

    if not blobs:
        print("✅ No images to migrate (bucket is empty or already migrated)")
        return

    print(f"📦 Found {len(blobs)} images in old structure\n")

    migrated_count = 0
    skipped_count = 0
    error_count = 0

    for blob in blobs:
        old_path = blob.name
        print(f"🔄 Processing: {old_path}")

        # Parse the old path: profile-pictures/{member_id}/{uuid}.jpg
        parts = old_path.split("/")
        if len(parts) != 3:
            print("  ⚠️  Unexpected path format, skipping")
            skipped_count += 1
            continue

        member_id = parts[1]
        filename = parts[2]

        # Get the member's space
        space_id = get_member_space(db, member_id)
        if not space_id:
            print("  ❌ Could not determine space, skipping")
            error_count += 1
            continue

        # New path: {space_id}/profile-pictures/{member_id}/{uuid}.jpg
        new_path = f"{space_id}/profile-pictures/{member_id}/{filename}"

        # Check if new path already exists
        new_blob = bucket.blob(new_path)
        if new_blob.exists():
            print(f"  ℹ️  Already exists at new location: {new_path}")
            skipped_count += 1
            continue

        if dry_run:
            print(f"  [DRY RUN] Would copy to: {new_path}")
            migrated_count += 1
        else:
            try:
                # Copy to new location
                bucket.copy_blob(blob, bucket, new_path)
                print(f"  ✅ Copied to: {new_path}")

                # Generate new signed URL
                new_signed_url = new_blob.generate_signed_url(
                    version="v4",
                    expiration=timedelta(days=7),
                    method="GET",
                )

                # Update member document with new URL
                member_ref = db.collection("members").document(member_id)
                member_ref.update({"profile_picture_url": new_signed_url})
                print("  ✅ Updated member document with new URL")

                # Delete old blob
                blob.delete()
                print("  🗑️  Deleted old image")

                migrated_count += 1

            except Exception as e:
                print(f"  ❌ Error: {e}")
                error_count += 1

        print()

    # Summary
    print("=" * 60)
    print("📊 Migration Summary:")
    print(f"  ✅ Migrated: {migrated_count}")
    print(f"  ⏭️  Skipped: {skipped_count}")
    print(f"  ❌ Errors: {error_count}")
    print("=" * 60)

    if dry_run:
        print("\n💡 Run with --live to perform actual migration")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Migrate profile pictures to space-organized structure"
    )
    parser.add_argument(
        "--live",
        action="store_true",
        help="Perform actual migration (default is dry-run)",
    )
    args = parser.parse_args()

    migrate_profile_pictures(dry_run=not args.live)
