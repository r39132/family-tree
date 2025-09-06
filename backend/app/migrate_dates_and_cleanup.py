"""
Data migration script to:
1. Convert all date fields to epoch timestamps (GMT)
2. Remove suspension-related fields from users collection
3. Clean up any legacy timestamp formats

Run with: python -m app.migrate_dates_and_cleanup
"""

import time
from datetime import datetime
from typing import Any, Optional

from google.cloud import firestore

from .firestore_client import get_db


def parse_firestore_timestamp(value: Any) -> Optional[int]:
    """Convert various timestamp formats to epoch seconds."""
    if value is None:
        return None

    # Already epoch seconds (int)
    if isinstance(value, int):
        return value

    # Float epoch seconds
    if isinstance(value, float):
        return int(value)

    # Firestore Timestamp
    if hasattr(value, "seconds"):
        return value.seconds

    # Python datetime
    if isinstance(value, datetime):
        return int(value.timestamp())

    # String ISO format
    if isinstance(value, str):
        try:
            dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
            return int(dt.timestamp())
        except Exception:
            print(f"Warning: Could not parse date string: {value}")
            return None

    print(f"Warning: Unknown timestamp format: {type(value)} - {value}")
    return None


def migrate_users_collection():
    """Migrate users collection: convert dates and remove suspension fields."""
    db = get_db()
    users_ref = db.collection("users")

    print("Starting users collection migration...")

    docs_processed = 0
    docs_updated = 0

    # Process all user documents
    docs = users_ref.stream()

    for doc in docs:
        docs_processed += 1
        data = doc.to_dict() or {}
        updates = {}
        fields_to_delete = []

        # Convert date fields to epoch seconds
        date_fields = ["created_at", "first_login_at", "last_login_at"]
        for field in date_fields:
            if field in data:
                epoch_value = parse_firestore_timestamp(data[field])
                if epoch_value is not None and epoch_value != data[field]:
                    updates[field] = epoch_value
                    print(f"  Converting {field} for user {doc.id}: {data[field]} -> {epoch_value}")

        # Handle evicted_at (might be stored as sessions_invalid_after timestamp)
        if "sessions_invalid_after" in data and data["sessions_invalid_after"]:
            # Convert sessions_invalid_after to evicted_at epoch timestamp
            evicted_epoch = parse_firestore_timestamp(data["sessions_invalid_after"])
            if evicted_epoch:
                updates["evicted_at"] = evicted_epoch
                print(
                    f"  Converting sessions_invalid_after to evicted_at for user {doc.id}: {evicted_epoch}"
                )

        # Remove suspension-related fields
        suspension_fields = ["suspended", "suspension_reason", "suspended_at", "suspended_by"]
        for field in suspension_fields:
            if field in data:
                fields_to_delete.append(field)
                print(f"  Removing suspension field '{field}' from user {doc.id}")

        # Apply updates if any
        if updates or fields_to_delete:
            try:
                # Apply field updates
                if updates:
                    doc.reference.update(updates)

                # Delete unwanted fields
                if fields_to_delete:
                    delete_updates = {field: firestore.DELETE_FIELD for field in fields_to_delete}
                    doc.reference.update(delete_updates)

                docs_updated += 1
                print(f"  ✅ Updated user {doc.id}")

            except Exception as e:
                print(f"  ❌ Error updating user {doc.id}: {e}")

        # Progress indicator
        if docs_processed % 10 == 0:
            print(f"Processed {docs_processed} users, updated {docs_updated}")

    print(f"Users migration complete: {docs_processed} processed, {docs_updated} updated")


def migrate_invites_collection():
    """Migrate invites collection: convert date fields to epoch timestamps."""
    db = get_db()
    invites_ref = db.collection("invites")

    print("Starting invites collection migration...")

    docs_processed = 0
    docs_updated = 0

    for doc in invites_ref.stream():
        docs_processed += 1
        data = doc.to_dict() or {}
        updates = {}

        # Convert date fields to epoch seconds
        date_fields = ["created_at", "used_at", "sent_at", "redeemed_at", "invited_at"]
        for field in date_fields:
            if field in data:
                epoch_value = parse_firestore_timestamp(data[field])
                if epoch_value is not None and epoch_value != data[field]:
                    updates[field] = epoch_value
                    print(
                        f"  Converting {field} for invite {doc.id}: {data[field]} -> {epoch_value}"
                    )

        # Apply updates if any
        if updates:
            try:
                doc.reference.update(updates)
                docs_updated += 1
                print(f"  ✅ Updated invite {doc.id}")
            except Exception as e:
                print(f"  ❌ Error updating invite {doc.id}: {e}")

    print(f"Invites migration complete: {docs_processed} processed, {docs_updated} updated")


def migrate_admin_logs_collection():
    """Migrate admin_logs collection: convert timestamp to epoch seconds."""
    db = get_db()
    logs_ref = db.collection("admin_logs")

    print("Starting admin_logs collection migration...")

    docs_processed = 0
    docs_updated = 0

    for doc in logs_ref.stream():
        docs_processed += 1
        data = doc.to_dict() or {}
        updates = {}

        # Convert timestamp field
        if "timestamp" in data:
            epoch_value = parse_firestore_timestamp(data["timestamp"])
            if epoch_value is not None and epoch_value != data["timestamp"]:
                updates["timestamp"] = epoch_value
                print(
                    f"  Converting timestamp for log {doc.id}: {data['timestamp']} -> {epoch_value}"
                )

        # Apply updates if any
        if updates:
            try:
                doc.reference.update(updates)
                docs_updated += 1
                print(f"  ✅ Updated admin log {doc.id}")
            except Exception as e:
                print(f"  ❌ Error updating admin log {doc.id}: {e}")

    print(f"Admin logs migration complete: {docs_processed} processed, {docs_updated} updated")


def migrate_members_collection():
    """Migrate members collection: convert dob_ts if it exists."""
    db = get_db()
    members_ref = db.collection("members")

    print("Starting members collection migration...")

    docs_processed = 0
    docs_updated = 0

    for doc in members_ref.stream():
        docs_processed += 1
        data = doc.to_dict() or {}
        updates = {}

        # Convert dob_ts field if it exists
        if "dob_ts" in data:
            epoch_value = parse_firestore_timestamp(data["dob_ts"])
            if epoch_value is not None and epoch_value != data["dob_ts"]:
                updates["dob_ts"] = epoch_value
                print(f"  Converting dob_ts for member {doc.id}: {data['dob_ts']} -> {epoch_value}")

        # Apply updates if any
        if updates:
            try:
                doc.reference.update(updates)
                docs_updated += 1
                print(f"  ✅ Updated member {doc.id}")
            except Exception as e:
                print(f"  ❌ Error updating member {doc.id}: {e}")

    print(f"Members migration complete: {docs_processed} processed, {docs_updated} updated")


def main():
    """Run the complete migration."""
    print("=" * 60)
    print("FAMILY TREE DATA MIGRATION")
    print("Converting dates to epoch timestamps and removing suspension fields")
    print("=" * 60)

    start_time = time.time()

    try:
        # Migrate each collection
        migrate_users_collection()
        print()
        migrate_invites_collection()
        print()
        migrate_admin_logs_collection()
        print()
        migrate_members_collection()

        elapsed = time.time() - start_time
        print("=" * 60)
        print(f"✅ Migration completed successfully in {elapsed:.2f} seconds")
        print("=" * 60)

    except Exception as e:
        print("=" * 60)
        print(f"❌ Migration failed: {e}")
        print("=" * 60)
        raise


if __name__ == "__main__":
    main()
