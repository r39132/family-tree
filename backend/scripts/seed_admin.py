"""Seed an admin user as per issue #33.

Promotes username 'sanand' (email 'sanand@apache.org') to admin if the user exists.
If the user does not exist, creates it with a temporary password to be reset by the user.
"""

from .auth_utils import hash_password
from .firestore_client import get_db


def main():
    db = get_db()
    user_ref = db.collection("users").document("sanand")
    doc = user_ref.get()
    if not doc.exists:
        print("Creating user 'sanand' with email 'sanand@apache.org'")
        import time

        tmp_pw = "ChangeMe!123"
        user_ref.set(
            {
                "email": "sanand@apache.org",
                "password_hash": hash_password(tmp_pw),
                "created_at": int(time.time()),  # Epoch seconds
                "roles": ["admin"],
                "sessions_invalid_after": None,
                "first_login_at": None,
                "last_login_at": None,
                "login_count": 0,
            }
        )
        print("User created. Temporary password:", tmp_pw)
        return
    data = doc.to_dict() or {}
    roles = data.get("roles", []) or []
    if "admin" not in roles:
        roles.append("admin")
        user_ref.update({"roles": roles})
        print("Promoted existing user 'sanand' to admin")
    else:
        print("User 'sanand' is already admin")


if __name__ == "__main__":
    main()
