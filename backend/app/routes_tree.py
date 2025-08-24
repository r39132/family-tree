from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from google.api_core.exceptions import AlreadyExists

from .deps import get_current_username
from .firestore_client import get_db
from .models import CreateMember, Member, MoveRequest, SpouseRequest, UpdateMember


def _name_key(first_name: str, last_name: str) -> str:
    return f"{(first_name or '').strip().lower()}|{(last_name or '').strip().lower()}"


router = APIRouter(prefix="/tree", tags=["tree"])


def _ensure_auth_header(request: Request):
    # Some tests override the auth dependency; still enforce that the header is present.
    if "authorization" not in request.headers:
        raise HTTPException(status_code=403, detail="Not authenticated")


@router.get("", response_model=Dict[str, Any])
def get_tree(request: Request, username: str = Depends(get_current_username)):
    _ensure_auth_header(request)
    db = get_db()
    members = {doc.id: doc.to_dict() | {"id": doc.id} for doc in db.collection("members").stream()}
    relations = [(d.id, d.to_dict()) for d in db.collection("relations").stream()]
    children: Dict[Optional[str], List[str]] = {}
    for rid, rel in relations:
        parent = rel.get("parent_id")
        child = rel.get("child_id")
        children.setdefault(parent, []).append(child)
    # Spousal links: if spouse_id is set, link nodes as partners at display time
    spouse_of: Dict[str, Optional[str]] = {}
    for mid, m in members.items():
        sid = m.get("spouse_id")
        if sid:
            spouse_of[mid] = sid

    def build(node_id: Optional[str]):
        built = []
        seen: set[str] = set()
        # Include children of this node AND of its spouse (to represent couple's children)
        parent_partner_id = spouse_of.get(node_id) if node_id else None
        combined_children = list(
            dict.fromkeys(
                (children.get(node_id, []) or []) + (children.get(parent_partner_id, []) or [])
            )
        )
        for cid in combined_children:
            if cid in seen:
                continue
            node_member = members[cid]
            partner_id = spouse_of.get(cid)
            node = {"member": node_member, "children": build(cid)}
            if partner_id and partner_id in members:
                # attach spouse but avoid duplicating
                node["spouse"] = members[partner_id]
                seen.add(partner_id)
            seen.add(cid)
            built.append(node)
        return built

    # Roots: explicitly parent_id None OR members with no relation at all,
    # but exclude a member from roots if their spouse is a child elsewhere (so they pair under the spouse)
    related_children = {c for cl in children.values() for c in cl}
    explicit_roots = children.get(None, [])
    no_relation = [
        mid for mid in members.keys() if mid not in related_children and mid not in explicit_roots
    ]
    filtered_no_relation = []
    for mid in no_relation:
        sid = spouse_of.get(mid)
        if sid and sid in related_children:
            # spouse is already a child -> this member should not become a separate root
            continue
        filtered_no_relation.append(mid)
    root_ids = list(dict.fromkeys(explicit_roots + filtered_no_relation))  # preserve order, unique
    # Build roots with spouse pairing and avoid duplicates
    roots = []
    seen_roots: set[str] = set()
    for rid in root_ids:
        if rid in seen_roots:
            continue
        node = {"member": members[rid], "children": build(rid)}
        partner_id = spouse_of.get(rid)
        if partner_id and partner_id in members:
            node["spouse"] = members[partner_id]
            seen_roots.add(partner_id)
        seen_roots.add(rid)
        roots.append(node)
    return {"roots": roots, "members": list(members.values())}


@router.post("/members", response_model=Member)
def create_member(
    member: CreateMember, request: Request, username: str = Depends(get_current_username)
):
    _ensure_auth_header(request)
    db = get_db()
    key = _name_key(member.first_name, member.last_name)
    key_ref = db.collection("member_keys").document(key)
    try:
        # Ensure uniqueness by creating a guard doc; fails if exists
        key_ref.create({"_": True})
    except AlreadyExists:
        raise HTTPException(
            status_code=409, detail="Member with same first_name and last_name already exists"
        )
    doc_ref = db.collection("members").document()
    data = member.model_dump(exclude={"id"}) | {"name_key": key}
    # derive timestamp field from MM/DD/YYYY
    try:
        dob_dt = datetime.strptime(member.dob, "%m/%d/%Y").replace(tzinfo=timezone.utc)
        data["dob_ts"] = dob_dt
    except Exception:
        pass
    try:
        doc_ref.set(data)
        key_ref.set({"member_id": doc_ref.id})
    except Exception:
        # rollback key if member write fails
        try:
            key_ref.delete()
        except Exception:
            pass
        raise
    return Member(id=doc_ref.id, **data)


@router.patch("/members/{member_id}", response_model=Member)
def update_member(
    member_id: str,
    member: UpdateMember,
    request: Request,
    username: str = Depends(get_current_username),
):
    _ensure_auth_header(request)
    db = get_db()
    ref = db.collection("members").document(member_id)
    if not ref.get().exists:
        raise HTTPException(status_code=404, detail="Member not found")
    current = ref.get().to_dict() or {}
    data = member.model_dump(exclude_unset=True)
    # If dob is present, recompute dob_ts
    if "dob" in data and data.get("dob"):
        try:
            dob_dt = datetime.strptime(data["dob"], "%m/%d/%Y").replace(tzinfo=timezone.utc)
            data["dob_ts"] = dob_dt
        except Exception:
            pass
    # Handle potential rename with uniqueness
    new_first = data.get("first_name", current.get("first_name"))
    new_last = data.get("last_name", current.get("last_name"))
    old_key = current.get("name_key") or _name_key(
        current.get("first_name", ""), current.get("last_name", "")
    )
    new_key = _name_key(new_first, new_last)
    if new_key != old_key:
        key_ref = db.collection("member_keys").document(new_key)
        # Attempt to reserve new key
        try:
            key_ref.create({"member_id": member_id})
        except AlreadyExists:
            # If it belongs to this member, allow; else conflict
            doc = key_ref.get()
            if doc.exists and (doc.to_dict() or {}).get("member_id") != member_id:
                raise HTTPException(
                    status_code=409,
                    detail="Member with same first_name and last_name already exists",
                )
        # Update member and swap keys
        data["name_key"] = new_key
        ref.update(data)
        # Remove old key if different
        if old_key:
            try:
                db.collection("member_keys").document(old_key).delete()
            except Exception:
                pass
    else:
        ref.update(data)
    new = ref.get().to_dict()
    return Member(id=member_id, **new)


@router.delete("/members/{member_id}")
def delete_member(member_id: str, request: Request, username: str = Depends(get_current_username)):
    _ensure_auth_header(request)
    db = get_db()
    # Ensure member has no children
    children = list(db.collection("relations").where("parent_id", "==", member_id).stream())
    if children:
        raise HTTPException(status_code=400, detail="Cannot delete: member has children")
    db.collection("relations").where("child_id", "==", member_id).get()
    # Remove relation pointing to this as child
    for rel in db.collection("relations").where("child_id", "==", member_id).stream():
        db.collection("relations").document(rel.id).delete()
    # delete unique key doc
    mdoc = db.collection("members").document(member_id).get()
    if mdoc.exists:
        mk = (mdoc.to_dict() or {}).get("name_key")
        if mk:
            try:
                db.collection("member_keys").document(mk).delete()
            except Exception:
                pass
    db.collection("members").document(member_id).delete()
    return {"ok": True}


@router.post("/members/{member_id}/spouse")
def set_spouse(
    member_id: str,
    req: SpouseRequest,
    request: Request,
    username: str = Depends(get_current_username),
):
    _ensure_auth_header(request)
    db = get_db()
    ref = db.collection("members").document(member_id)
    mdoc = ref.get()
    if not mdoc.exists:
        raise HTTPException(status_code=404, detail="Member not found")
    # Unlink existing spouse if any
    curr = mdoc.to_dict() or {}
    current_spouse = curr.get("spouse_id")
    spouse_id = req.spouse_id
    if spouse_id is None and current_spouse:
        sref = db.collection("members").document(current_spouse)
        if sref.get().exists:
            sref.update({"spouse_id": None})
        ref.update({"spouse_id": None})
        return {"ok": True}
    # Link both sides for convenience
    ref.update({"spouse_id": spouse_id})
    if spouse_id:
        sref = db.collection("members").document(spouse_id)
        if sref.get().exists:
            sref.update({"spouse_id": member_id})
    return {"ok": True}


@router.post("/move")
def move(req: MoveRequest, request: Request, username: str = Depends(get_current_username)):
    _ensure_auth_header(request)
    db = get_db()
    # Remove any existing parent relation for child
    for rel in db.collection("relations").where("child_id", "==", req.child_id).stream():
        db.collection("relations").document(rel.id).delete()
    # Set new parent (None -> root)
    db.collection("relations").add({"child_id": req.child_id, "parent_id": req.new_parent_id})
    return {"ok": True}
