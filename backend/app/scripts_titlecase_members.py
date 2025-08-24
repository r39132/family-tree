from .firestore_client import get_db

FIELDS = [
    "first_name",
    "nick_name",
    "middle_name",
    "last_name",
    "birth_location",
    "residence_location",
    "email",
    "phone",
    # hobbies handled separately
]


def to_title(s: str) -> str:
    return " ".join(w.capitalize() for w in (s or "").split())


def main():
    db = get_db()
    members = list(db.collection("members").stream())
    count = 0
    for doc in members:
        data = doc.to_dict() or {}
        updates = {}
        for f in FIELDS:
            v = data.get(f)
            if isinstance(v, str) and v.strip():
                t = to_title(v)
                if t != v:
                    updates[f] = t
        if isinstance(data.get("hobbies"), list):
            hobbies = [to_title(x) if isinstance(x, str) else x for x in data.get("hobbies", [])]
            if hobbies != data.get("hobbies"):
                updates["hobbies"] = hobbies
        if updates:
            doc.reference.update(updates)
            count += 1
    print(f"Updated {count} members with title-cased fields")


if __name__ == "__main__":
    main()
