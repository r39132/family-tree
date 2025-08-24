"""
One-off migration: convert member.dob from DD/MM/YYYY to MM/DD/YYYY where applicable.
Run with: uv run python -m app.scripts_migrate_dob_format
"""
from app.firestore_client import get_db
from datetime import datetime

def is_ddmmyyyy(s: str) -> bool:
    try:
        datetime.strptime(s, "%d/%m/%Y")
        return True
    except Exception:
        return False

def to_mmddyyyy(s: str) -> str:
    dt = datetime.strptime(s, "%d/%m/%Y")
    return dt.strftime("%m/%d/%Y")

def main():
    db = get_db()
    batch = db.batch()
    count = 0
    for doc in db.collection("members").stream():
        data = doc.to_dict() or {}
        dob = data.get("dob")
        if isinstance(dob, str) and is_ddmmyyyy(dob):
            new_dob = to_mmddyyyy(dob)
            batch.update(db.collection("members").document(doc.id), {"dob": new_dob})
            count += 1
            # Commit in chunks of 400 to avoid batch limits
            if count % 400 == 0:
                batch.commit()
                batch = db.batch()
    if count % 400:
        batch.commit()
    print(f"Updated {count} documents.")

if __name__ == "__main__":
    main()
