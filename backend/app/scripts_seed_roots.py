from .firestore_client import get_db
from .routes_tree import _name_key

def ensure_member(first_name: str, last_name: str, dob: str | None = None) -> str:
    db = get_db()
    key = _name_key(first_name, last_name)
    # check by name key
    kdoc = db.collection("member_keys").document(key).get()
    if kdoc.exists:
        mid = (kdoc.to_dict() or {}).get("member_id")
        if mid:
            return mid
    # create member
    mref = db.collection("members").document()
    data = {"first_name": first_name, "last_name": last_name, "dob": dob or None, "name_key": key}
    mref.set(data)
    db.collection("member_keys").document(key).set({"member_id": mref.id})
    # Make it a root explicitly if not already
    existing_roots = list(db.collection("relations").where("child_id", "==", mref.id).where("parent_id", "==", None).stream())
    if not existing_roots:
        db.collection("relations").add({"parent_id": None, "child_id": mref.id})
    return mref.id

def main():
    achan_id = ensure_member("Achan", "Root", dob=None)
    nanan_id = ensure_member("Nanan", "Root", dob=None)
    print("Seeded roots:", achan_id, nanan_id)

if __name__ == "__main__":
    main()
