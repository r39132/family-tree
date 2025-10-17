"""Seed an admin user as per issue #33.

Promotes a user to admin if the user exists.
If the user does not exist, creates it with the specified password.
"""

import argparse
import time

from .auth_utils import hash_password
from .firestore_client import get_db


def main(username: str, email: str, password: str):
    """Create or promote a user to admin.

    Args:
        username: The username for the admin account
        email: The email address for the admin account
        password: The password for the admin account
    """
    db = get_db()
    user_ref = db.collection("users").document(username)
    doc = user_ref.get()
    if not doc.exists:
        print(f"Creating user '{username}' with email '{email}'")
        user_ref.set(
            {
                "email": email,
                "password_hash": hash_password(password),
                "created_at": int(time.time()),  # Epoch seconds
                "roles": ["admin"],
                "sessions_invalid_after": None,
                "first_login_at": None,
                "last_login_at": None,
                "login_count": 0,
            }
        )
        print("User created. Password:", password)
        return
    data = doc.to_dict() or {}
    roles = data.get("roles", []) or []
    if "admin" not in roles:
        roles.append("admin")
        user_ref.update({"roles": roles})
        print(f"Promoted existing user '{username}' to admin")
    else:
        print(f"User '{username}' is already admin")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Create or promote a user to admin role")
    parser.add_argument(
        "--username", default="sanand", help="Username for the admin account (default: sanand)"
    )
    parser.add_argument(
        "--email",
        default="sanand@apache.org",
        help="Email address for the admin account (default: sanand@apache.org)",
    )
    parser.add_argument(
        "--password",
        default="ChangeMe!123",
        help="Password for the admin account (default: ChangeMe!123)",
    )

    args = parser.parse_args()
    main(args.username, args.email, args.password)
