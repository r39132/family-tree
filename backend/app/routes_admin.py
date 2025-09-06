from datetime import datetime, timezone
from typing import List

from fastapi import APIRouter, Depends, HTTPException

from .deps import get_current_username
from .firestore_client import get_db

router = APIRouter(prefix="/admin", tags=["admin"])


def require_admin(current_user: str = Depends(get_current_username)) -> str:
    db = get_db()
    doc = db.collection("users").document(current_user).get()
    if not doc.exists:
        raise HTTPException(status_code=404, detail="User not found")
    data = doc.to_dict() or {}
    roles: List[str] = data.get("roles", []) or []
    if "admin" not in roles:
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user


def log_admin_action(actor: str, action: str, target: str, extra: dict | None = None):
    db = get_db()
    payload = {
        "actor": actor,
        "action": action,
        "target": target,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    if extra:
        payload.update({f"extra_{k}": v for k, v in extra.items()})
    db.collection("admin_logs").add(payload)


@router.get("/users")
def list_users(_admin: str = Depends(require_admin)):
    db = get_db()
    users = []
    for d in db.collection("users").stream():
        x = d.to_dict() or {}
        users.append(
            {
                "id": d.id,
                "email": x.get("email"),
                "first_login_at": x.get("first_login_at"),  # Now epoch seconds
                "last_login_at": x.get("last_login_at"),  # Now epoch seconds
                "login_count": x.get("login_count", 0),
                "evicted_at": x.get("evicted_at"),  # Now epoch seconds
                "is_admin": "admin" in (x.get("roles", []) or []),
            }
        )
    # Stable sort by id
    users.sort(key=lambda u: u["id"])
    return {"ok": True, "users": users}


@router.post("/users/{user_id}/evict")
def evict_user(user_id: str, admin: str = Depends(require_admin)):
    db = get_db()
    ref = db.collection("users").document(user_id)
    if not ref.get().exists:
        raise HTTPException(status_code=404, detail="User not found")
    # Invalidate all existing sessions by setting cutoff
    import time

    evicted_at = int(time.time())
    ref.update(
        {"sessions_invalid_after": datetime.now(timezone.utc).isoformat(), "evicted_at": evicted_at}
    )
    log_admin_action(admin, "evict", user_id, {"evicted_at": evicted_at})
    return {"ok": True}


@router.post("/users/{user_id}/unevict")
def unevict_user(user_id: str, admin: str = Depends(require_admin)):
    db = get_db()
    ref = db.collection("users").document(user_id)
    if not ref.get().exists:
        raise HTTPException(status_code=404, detail="User not found")
    # Clear the session invalidation cutoff and evicted timestamp
    ref.update({"sessions_invalid_after": None, "evicted_at": None})
    log_admin_action(admin, "unevict", user_id, {})
    return {"ok": True}


@router.post("/users/{user_id}/promote")
def promote_admin(user_id: str, admin: str = Depends(require_admin)):
    db = get_db()
    ref = db.collection("users").document(user_id)
    doc = ref.get()
    if not doc.exists:
        raise HTTPException(status_code=404, detail="User not found")
    roles = (doc.to_dict() or {}).get("roles", []) or []
    if "admin" not in roles:
        roles.append("admin")
        ref.update({"roles": roles})
    log_admin_action(admin, "promote", user_id, {"roles": roles})
    return {"ok": True}


@router.post("/users/{user_id}/demote")
def demote_admin(user_id: str, admin: str = Depends(require_admin)):
    db = get_db()
    ref = db.collection("users").document(user_id)
    doc = ref.get()
    if not doc.exists:
        raise HTTPException(status_code=404, detail="User not found")
    roles = (doc.to_dict() or {}).get("roles", []) or []
    roles = [r for r in roles if r != "admin"]
    ref.update({"roles": roles})
    log_admin_action(admin, "demote", user_id, {"roles": roles})
    return {"ok": True}
