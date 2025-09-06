#!/usr/bin/env python3
"""
Migration script to add invited_at and redeemed_at columns to invites.
This script will:
1. Add invited_at field (copy of sent_at for existing records)
2. Add redeemed_at field (copy of used_at for existing records)
"""

import sys

sys.path.append("/Users/r39132/Projects/family-tree/backend")

from app.firestore_client import get_db


def migrate_invite_dates():
    """Migrate existing invite records to include new date fields"""
    print("🔄 Starting invite dates migration...")

    db = get_db()

    # Get all invites
    invites_ref = db.collection("invites")
    docs = list(invites_ref.stream())

    print(f"Found {len(docs)} invites to migrate")

    updated_count = 0

    for doc in docs:
        doc_id = doc.id
        data = doc.to_dict()

        updates = {}

        # Add invited_at field if sent_at exists but invited_at doesn't
        if data.get("sent_at") and not data.get("invited_at"):
            updates["invited_at"] = data["sent_at"]
            print(f"  Adding invited_at for invite {doc_id}")

        # Add redeemed_at field if used_at exists but redeemed_at doesn't
        if data.get("used_at") and not data.get("redeemed_at"):
            updates["redeemed_at"] = data["used_at"]
            print(f"  Adding redeemed_at for invite {doc_id}")

        # Apply updates if any
        if updates:
            doc.reference.update(updates)
            updated_count += 1
            print(f"  ✅ Updated invite {doc_id}")

    print(f"🎉 Migration complete! Updated {updated_count} invite records")


if __name__ == "__main__":
    migrate_invite_dates()
