"""
Backfill dob_ts (Firestore timestamp) from dob string (MM/DD/YYYY) for existing member docs.
Run with: uv run python -m app.scripts_backfill_dob_ts
"""
from app.firestore_client import get_db
from datetime import datetime, timezone

def is_mmddyyyy(s: str) -> bool:
    try:
        datetime.strptime(s, "%m/%d/%Y")
        return True
    except Exception:
        return False

def main():
    db = get_db()
    batch = db.batch()
    count = 0
    for doc in db.collection("members").stream():
        data = doc.to_dict() or {}
        if data.get("dob_ts"):
            continue
        dob = data.get("dob")
        if isinstance(dob, str) and is_mmddyyyy(dob):
            ts = datetime.strptime(dob, "%m/%d/%Y").replace(tzinfo=timezone.utc)
            batch.update(db.collection("members").document(doc.id), {"dob_ts": ts})
            count += 1
            if count % 400 == 0:
                batch.commit()
                batch = db.batch()
    if count % 400:
        batch.commit()
    print(f"Backfilled dob_ts for {count} members.")

if __name__ == "__main__":
    main()
