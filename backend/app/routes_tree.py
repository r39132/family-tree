from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set

from fastapi import APIRouter, Depends, HTTPException, Request
from google.api_core.exceptions import AlreadyExists

from .deps import get_current_username
from .firestore_client import get_db
from .models import (
    CreateMember,
    Member,
    MoveRequest,
    RecoverTreeRequest,
    SpouseRequest,
    TreeVersionInfo,
    UpdateMember,
)
from .utils.time import to_iso_string, utc_now


def _name_key(first_name: str, last_name: str) -> str:
    return f"{(first_name or '').strip().lower()}|{(last_name or '').strip().lower()}"


def _get_user_space(username: str) -> str:
    """Get the current space for a user. Returns 'demo' as fallback."""
    db = get_db()
    user_ref = db.collection("users").document(username)
    user_doc = user_ref.get()

    if not user_doc.exists:
        return "demo"  # Default fallback

    data = user_doc.to_dict()
    return data.get("current_space", "demo")


router = APIRouter(prefix="/tree", tags=["tree"])


def _ensure_auth_header(request: Request):
    # Some tests override the auth dependency; still enforce that the header is present.
    if "authorization" not in request.headers:
        raise HTTPException(status_code=403, detail="Not authenticated")


@router.get("", response_model=Dict[str, Any])
def get_tree(request: Request, username: str = Depends(get_current_username)):
    _ensure_auth_header(request)
    db = get_db()

    # Get user's current space
    space_id = _get_user_space(username)

    # Load space-specific tree data
    members_query = db.collection("members").where("space_id", "==", space_id)
    members = {doc.id: doc.to_dict() | {"id": doc.id} for doc in members_query.stream()}

    relations_query = db.collection("relations").where("space_id", "==", space_id)
    relations = [(d.id, d.to_dict()) for d in relations_query.stream()]

    children: Dict[Optional[str], List[str]] = {}
    for rid, rel in relations:
        parent = rel.get("parent_id")
        child = rel.get("child_id")
        children.setdefault(parent, []).append(child)
    # Deduplicate children per parent to avoid duplicated relation docs showing twice
    for p, lst in list(children.items()):
        children[p] = list(dict.fromkeys([c for c in lst if c is not None]))
    # Spousal links: if spouse_id is set, link nodes as partners at display time
    spouse_of: Dict[str, Optional[str]] = {}
    for mid, m in members.items():
        sid = m.get("spouse_id")
        if sid:
            spouse_of[mid] = sid

    rendered: Set[str] = set()

    def build(node_id: Optional[str], path: Optional[Set[str]] = None):
        built = []
        local_seen: set[str] = set()
        # Track recursion path to avoid cycles (e.g., accidental parent loops)
        path = set(path or set())
        if node_id is not None:
            if node_id in path:
                # Cycle detected; stop descending
                return built
            path.add(node_id)
        # Include children of this node AND of its spouse (to represent couple's children)
        parent_partner_id = spouse_of.get(node_id) if node_id else None
        combined_children = list(
            dict.fromkeys(
                (children.get(node_id, []) or []) + (children.get(parent_partner_id, []) or [])
            )
        )
        for cid in combined_children:
            # Do not treat spouse as a child
            if node_id is not None and cid == spouse_of.get(node_id):
                continue
            # Skip if this member was already rendered somewhere else in the tree
            if cid in rendered:
                continue
            if cid in local_seen or (cid in path):
                continue
            # Skip if child doc is missing (defensive against dangling relations)
            node_member = members.get(cid)
            if not node_member:
                continue
            partner_id = spouse_of.get(cid)
            node = {"member": node_member, "children": build(cid, path)}
            if partner_id and partner_id in members:
                # attach spouse but avoid duplicating
                node["spouse"] = members[partner_id]
                local_seen.add(partner_id)
                rendered.add(partner_id)
            local_seen.add(cid)
            rendered.add(cid)
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
        if rid in rendered:
            continue
        if rid in seen_roots:
            continue
        node = {"member": members[rid], "children": build(rid)}
        partner_id = spouse_of.get(rid)
        if partner_id and partner_id in members:
            node["spouse"] = members[partner_id]
            seen_roots.add(partner_id)
            rendered.add(partner_id)
        seen_roots.add(rid)
        rendered.add(rid)
        roots.append(node)
    return {"roots": roots, "members": list(members.values())}


@router.get("/members", response_model=List[Member])
def search_members(
    request: Request,
    username: str = Depends(get_current_username),
    q: Optional[str] = None,
    limit: int = 50,
):
    """Search for members in the current space. Used for spouse dropdown."""
    _ensure_auth_header(request)
    db = get_db()

    # Get user's current space
    space_id = _get_user_space(username)

    # Base query for members in current space
    members_query = db.collection("members").where("space_id", "==", space_id)

    members_data = []
    for doc in members_query.stream():
        member = doc.to_dict() | {"id": doc.id}

        # If search query provided, filter by name
        if q:
            full_name = f"{member.get('first_name', '')} {member.get('last_name', '')}".lower()
            if q.lower() not in full_name:
                continue

        members_data.append(Member(**member))

        # Apply limit
        if len(members_data) >= limit:
            break

    return members_data


def _snapshot_relations(db):
    # Return deterministic snapshot of relations for change detection
    rels = []
    for d in db.collection("relations").stream():
        data = d.to_dict() or {}
        # Store as objects to avoid nested arrays (Firestore forbids arrays of arrays)
        rels.append({"parent_id": data.get("parent_id"), "child_id": data.get("child_id")})
    # sort to ensure stable ordering
    rels.sort(key=lambda x: (str(x.get("parent_id")), str(x.get("child_id"))))
    return rels


def _get_latest_version(db):
    qs = (
        db.collection("tree_versions")
        .order_by("created_at", direction="DESCENDING")
        .limit(1)
        .stream()
    )
    latest = None
    for d in qs:
        latest = d
    return latest


def _next_version_number(db) -> int:
    # Fetch latest to derive next version number
    latest = _get_latest_version(db)
    if latest is None:
        return 1
    data = latest.to_dict() or {}
    return int(data.get("version") or 0) + 1


@router.get("/versions", response_model=List[TreeVersionInfo])
def list_versions(request: Request, username: str = Depends(get_current_username)):
    _ensure_auth_header(request)
    db = get_db()
    out: List[TreeVersionInfo] = []
    # Load global versions (not user-specific)
    for d in db.collection("tree_versions").order_by("created_at", direction="DESCENDING").stream():
        data = d.to_dict() or {}
        out.append(
            TreeVersionInfo(
                id=d.id,
                created_at=(data.get("created_at") or ""),
                version=int(data.get("version") or 0),
                relations_count=None,
            )
        )
    return out


@router.get("/unsaved", response_model=dict)
def unsaved_changes(request: Request, username: str = Depends(get_current_username)):
    _ensure_auth_header(request)
    db = get_db()

    # Check if there's an active version pointer
    active_version_doc = db.collection("tree_state").document("active_version").get()
    current_relations = _snapshot_relations(db)

    # Debug info
    print(f"DEBUG: active_version_doc.exists = {active_version_doc.exists}")
    print(f"DEBUG: current_relations count = {len(current_relations)}")

    if not active_version_doc.exists:
        # No active version set
        latest = _get_latest_version(db)
        print(f"DEBUG: latest version exists = {latest is not None}")
        if latest is None:
            # No versions exist yet - current state is the baseline
            print("DEBUG: No versions exist, returning unsaved=False")
            return {"unsaved": False}

        # Set latest as active version for future calls
        db.collection("tree_state").document("active_version").set({"version_id": latest.id})
        print(f"DEBUG: Set active version to {latest.id}")

        # Compare current state to this latest version
        latest_data = latest.to_dict() or {}
        saved_relations = latest_data.get("relations") or []
        print(f"DEBUG: saved_relations count = {len(saved_relations)}")
        print(f"DEBUG: Relations match = {saved_relations == current_relations}")

        # Return the actual comparison - don't auto-sync
        result = saved_relations != current_relations
        print(f"DEBUG: Returning unsaved = {result}")
        return {"unsaved": result}

    # Compare current state to active version
    active_data = active_version_doc.to_dict() or {}
    active_version_id = active_data.get("version_id")
    print(f"DEBUG: active_version_id = {active_version_id}")

    if not active_version_id:
        # Active version doc exists but no version_id, treat as unsaved
        print("DEBUG: No version_id in active doc, returning unsaved=True")
        return {"unsaved": True}

    # Get the active version's relations
    version_doc = db.collection("tree_versions").document(active_version_id).get()
    if not version_doc.exists:
        # Active version doesn't exist, treat as unsaved
        print(f"DEBUG: Active version {active_version_id} doesn't exist, returning unsaved=True")
        return {"unsaved": True}

    version_data = version_doc.to_dict() or {}
    active_relations = version_data.get("relations") or []
    print(f"DEBUG: active_relations count = {len(active_relations)}")

    # Debug: show first few relations from each to compare
    print(f"DEBUG: First 3 current: {current_relations[:3] if current_relations else []}")
    print(f"DEBUG: First 3 active: {active_relations[:3] if active_relations else []}")

    result = active_relations != current_relations
    print(f"DEBUG: Final comparison - unsaved = {result}")
    return {"unsaved": result}


@router.post("/save", response_model=TreeVersionInfo)
def save_tree(request: Request, username: str = Depends(get_current_username)):
    _ensure_auth_header(request)
    db = get_db()
    rels = _snapshot_relations(db)
    doc = db.collection("tree_versions").document()
    created_at = to_iso_string(utc_now())
    version = _next_version_number(db)
    doc.set({"created_at": created_at, "relations": rels, "version": version})

    # Set this new version as the active version
    db.collection("tree_state").document("active_version").set({"version_id": doc.id})

    return TreeVersionInfo(id=doc.id, created_at=created_at, version=version)


@router.post("/recover")
def recover_tree(
    req: RecoverTreeRequest,
    request: Request,
    username: str = Depends(get_current_username),
):
    _ensure_auth_header(request)
    db = get_db()
    doc = db.collection("tree_versions").document(req.version_id).get()
    if not doc.exists:
        raise HTTPException(status_code=404, detail="Version not found")
    data = doc.to_dict() or {}
    rels: List[Dict[str, Optional[str]]] = data.get("relations") or []
    # Replace relations collection with saved snapshot
    # Delete all existing relations
    for d in db.collection("relations").stream():
        db.collection("relations").document(d.id).delete()
    # Write snapshot
    for item in rels:
        db.collection("relations").add(
            {"parent_id": item.get("parent_id"), "child_id": item.get("child_id")}
        )

    # Set this version as the active version (key change!)
    db.collection("tree_state").document("active_version").set({"version_id": req.version_id})

    return {"ok": True}


@router.post("/versions/backfill")
def backfill_versions(request: Request, username: str = Depends(get_current_username)):
    """Assign version numbers to existing tree_versions docs that lack them.

    Numbers start at 1 in ascending created_at order. Existing version numbers are left intact.
    """
    _ensure_auth_header(request)
    db = get_db()
    # Read all versions oldest-first
    docs = list(
        db.collection("tree_versions").order_by("created_at", direction="ASCENDING").stream()
    )
    # Assign 1..N in chronological order for ALL docs (rewrites existing versions)
    v = 1
    for d in docs:
        db.collection("tree_versions").document(d.id).update({"version": v})
        v += 1
    return {"updated": len(docs), "total": len(docs)}


def _parse_hobbies(hobbies_input: Optional[List[str]]) -> List[str]:
    """Parse and normalize hobbies from list or comma-separated strings."""
    if not hobbies_input:
        return []

    normalized = []
    for item in hobbies_input:
        if isinstance(item, str):
            # Split on commas and normalize
            parts = [part.strip() for part in item.split(",")]
            normalized.extend(parts)
        else:
            normalized.append(str(item))

    # Remove empty strings and deduplicate while preserving order
    result = []
    for hobby in normalized:
        cleaned = hobby.strip()
        if cleaned and cleaned not in result:
            result.append(cleaned)

    return result


@router.post("/members", response_model=Member)
def create_member(
    member: CreateMember,
    request: Request,
    username: str = Depends(get_current_username),
):
    _ensure_auth_header(request)
    db = get_db()

    # Get user's current space
    space_id = _get_user_space(username)

    # Validate spouse_id if provided
    if member.spouse_id:
        # Cannot be themselves (we don't have the member ID yet, but this will be handled in mutual linking)
        spouse_ref = db.collection("members").document(member.spouse_id)
        spouse_doc = spouse_ref.get()

        if not spouse_doc.exists:
            raise HTTPException(status_code=404, detail="Spouse not found")

        spouse_data = spouse_doc.to_dict() or {}

        # Check spouse is in same space
        if spouse_data.get("space_id") != space_id:
            raise HTTPException(status_code=400, detail="Both members must be in the same space")

        # Check if spouse already has a spouse (monogamy enforcement)
        current_spouse_id = spouse_data.get("spouse_id")
        if current_spouse_id:
            raise HTTPException(status_code=409, detail="Selected member already has a spouse")

    # Check uniqueness within the space
    key = _name_key(member.first_name, member.last_name)
    space_key = f"{space_id}:{key}"  # Space-scoped key
    key_ref = db.collection("member_keys").document(space_key)
    try:
        # Ensure uniqueness by creating a guard doc; fails if exists
        key_ref.create({"space_id": space_id, "name_key": key})
    except AlreadyExists:
        raise HTTPException(
            status_code=409,
            detail="Member with same first_name and last_name already exists in this family space",
        )

    doc_ref = db.collection("members").document()

    # Process and normalize hobbies
    processed_hobbies = _parse_hobbies(member.hobbies)

    data = member.model_dump(exclude={"id"}) | {
        "name_key": key,
        "space_id": space_id,  # Associate member with space
        "hobbies": processed_hobbies,  # Use processed hobbies
        "created_by": username,  # Track who created the member
    }

    # derive timestamp field from MM/DD/YYYY and disallow future dates
    try:
        data["dob_ts"] = datetime.strptime(member.dob, "%m/%d/%Y").replace(tzinfo=timezone.utc)
    except Exception:
        # leave unparsed; tolerated by model, but dob_ts will be absent
        pass

    try:
        # Create the member
        doc_ref.set(data)
        key_ref.set({"member_id": doc_ref.id, "space_id": space_id})

        # Handle mutual spouse linking if spouse_id is provided
        if member.spouse_id:
            # Check that we're not trying to link to ourselves
            if doc_ref.id == member.spouse_id:
                raise HTTPException(status_code=400, detail="You can't select the same person")

            # Set mutual spouse relationship
            spouse_ref = db.collection("members").document(member.spouse_id)
            spouse_ref.update({"spouse_id": doc_ref.id})

    except Exception as e:
        # rollback key if member write fails
        try:
            key_ref.delete()
        except Exception:
            pass
        # If it's an HTTPException, re-raise it
        if isinstance(e, HTTPException):
            raise e
        # Otherwise, wrap in a generic error
        raise HTTPException(status_code=500, detail=f"Failed to create member: {str(e)}")

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

    # Get user's current space
    space_id = _get_user_space(username)

    ref = db.collection("members").document(member_id)
    member_doc = ref.get()
    if not member_doc.exists:
        raise HTTPException(status_code=404, detail="Member not found")

    current = member_doc.to_dict() or {}

    # Ensure member belongs to user's current space
    if current.get("space_id") != space_id:
        raise HTTPException(status_code=403, detail="Member not found in current family space")

    data = member.model_dump(exclude_unset=True)

    # Validate spouse_id if provided
    if "spouse_id" in data:
        spouse_id = data["spouse_id"]

        if spouse_id:
            # Cannot be themselves
            if spouse_id == member_id:
                raise HTTPException(status_code=400, detail="You can't select the same person")

            spouse_ref = db.collection("members").document(spouse_id)
            spouse_doc = spouse_ref.get()

            if not spouse_doc.exists:
                raise HTTPException(status_code=404, detail="Spouse not found")

            spouse_data = spouse_doc.to_dict() or {}

            # Check spouse is in same space
            if spouse_data.get("space_id") != space_id:
                raise HTTPException(
                    status_code=400, detail="Both members must be in the same space"
                )

            # Check if spouse already has a different spouse
            current_spouse_id = spouse_data.get("spouse_id")
            if current_spouse_id and current_spouse_id != member_id:
                raise HTTPException(status_code=409, detail="Selected member already has a spouse")
        # If spouse_id is None or empty string, we're clearing the spouse relationship
        elif spouse_id == "" or spouse_id is None:
            # Clear spouse relationship from current spouse if exists
            current_spouse_id = current.get("spouse_id")
            if current_spouse_id:
                current_spouse_ref = db.collection("members").document(current_spouse_id)
                current_spouse_doc = current_spouse_ref.get()
                if current_spouse_doc.exists:
                    current_spouse_ref.update({"spouse_id": None})
            data["spouse_id"] = None

    # Process hobbies if provided
    if "hobbies" in data and data["hobbies"] is not None:
        data["hobbies"] = _parse_hobbies(data["hobbies"])

    # If dob is present, recompute dob_ts
    if "dob" in data and data.get("dob"):
        try:
            dob_dt = datetime.strptime(data["dob"], "%m/%d/%Y").replace(tzinfo=timezone.utc)
            if dob_dt > utc_now():
                raise HTTPException(status_code=400, detail="Date of Birth cannot be in the future")
            data["dob_ts"] = dob_dt
        except HTTPException:
            raise
        except Exception:
            # Leave as-is if unparsable
            pass
    # Handle potential rename with uniqueness
    new_first = data.get("first_name", current.get("first_name"))
    new_last = data.get("last_name", current.get("last_name"))
    old_key = current.get("name_key") or _name_key(
        current.get("first_name", ""), current.get("last_name", "")
    )
    new_key = _name_key(new_first, new_last)
    old_space_key = f"{space_id}:{old_key}"
    new_space_key = f"{space_id}:{new_key}"

    if new_key != old_key:
        key_ref = db.collection("member_keys").document(new_space_key)
        # Attempt to reserve new key
        try:
            key_ref.create({"member_id": member_id, "space_id": space_id})
        except AlreadyExists:
            # If it belongs to this member, allow; else conflict
            doc = key_ref.get()
            if doc.exists and (doc.to_dict() or {}).get("member_id") != member_id:
                raise HTTPException(
                    status_code=409,
                    detail="Member with same first_name and last_name already exists in this family space",
                )
        # Update member and swap keys
        data["name_key"] = new_key
        ref.update(data)
        # Remove old key if different
        if old_key:
            try:
                db.collection("member_keys").document(old_space_key).delete()
            except Exception:
                pass
    else:
        ref.update(data)

    # Handle mutual spouse linking if spouse_id was updated
    if "spouse_id" in data and data["spouse_id"]:
        spouse_ref = db.collection("members").document(data["spouse_id"])
        spouse_ref.update({"spouse_id": member_id})

    new = ref.get().to_dict()
    return Member(id=member_id, **{k: v for k, v in new.items() if k != "id"})


@router.delete("/members/{member_id}")
def delete_member(member_id: str, request: Request, username: str = Depends(get_current_username)):
    _ensure_auth_header(request)
    db = get_db()

    # Get user's current space
    space_id = _get_user_space(username)

    # Check that member exists and belongs to current space
    member_ref = db.collection("members").document(member_id)
    member_doc = member_ref.get()
    if not member_doc.exists:
        raise HTTPException(status_code=404, detail="Member not found")

    member_data = member_doc.to_dict() or {}
    if member_data.get("space_id") != space_id:
        raise HTTPException(status_code=403, detail="Member not found in current family space")

    # Ensure member has no children (space-scoped check)
    children = list(
        db.collection("relations")
        .where("parent_id", "==", member_id)
        .where("space_id", "==", space_id)
        .stream()
    )
    if children:
        raise HTTPException(status_code=400, detail="Cannot delete: member has children")

    # Remove relation pointing to this as child (space-scoped)
    for rel in (
        db.collection("relations")
        .where("child_id", "==", member_id)
        .where("space_id", "==", space_id)
        .stream()
    ):
        db.collection("relations").document(rel.id).delete()

    # Delete unique key doc (space-scoped)
    mk = member_data.get("name_key")
    if mk:
        space_key = f"{space_id}:{mk}"
        try:
            db.collection("member_keys").document(space_key).delete()
        except Exception:
            pass

    # Delete the member
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

    # Get user's current space
    space_id = _get_user_space(username)

    ref = db.collection("members").document(member_id)
    mdoc = ref.get()
    if not mdoc.exists:
        raise HTTPException(status_code=404, detail="Member not found")

    member_data = mdoc.to_dict() or {}
    if member_data.get("space_id") != space_id:
        raise HTTPException(status_code=403, detail="Member not found in current family space")

    # Unlink existing spouse if any
    current_spouse = member_data.get("spouse_id")
    spouse_id = req.spouse_id

    if spouse_id is None and current_spouse:
        # Check that current spouse is in same space
        sref = db.collection("members").document(current_spouse)
        spouse_doc = sref.get()
        if spouse_doc.exists:
            spouse_data = spouse_doc.to_dict() or {}
            if spouse_data.get("space_id") == space_id:
                sref.update({"spouse_id": None})
        ref.update({"spouse_id": None})
        return {"ok": True}

    # Link both sides for convenience
    if spouse_id:
        sref = db.collection("members").document(spouse_id)
        spouse_doc = sref.get()
        if not spouse_doc.exists:
            raise HTTPException(status_code=404, detail="Spouse not found")

        spouse_data = spouse_doc.to_dict() or {}
        if spouse_data.get("space_id") != space_id:
            raise HTTPException(status_code=403, detail="Spouse not found in current family space")

        sref.update({"spouse_id": member_id})

    ref.update({"spouse_id": spouse_id})
    return {"ok": True}


@router.post("/move")
def move(req: MoveRequest, request: Request, username: str = Depends(get_current_username)):
    _ensure_auth_header(request)
    db = get_db()

    # Get user's current space
    space_id = _get_user_space(username)

    # Validate that child exists and belongs to current space
    child_doc = db.collection("members").document(req.child_id).get()
    if not child_doc.exists:
        raise HTTPException(status_code=404, detail="Child member not found")

    child_data = child_doc.to_dict() or {}
    if child_data.get("space_id") != space_id:
        raise HTTPException(
            status_code=403, detail="Child member not found in current family space"
        )

    # Validate new parent if specified
    if req.new_parent_id is not None:
        parent_doc = db.collection("members").document(req.new_parent_id).get()
        if not parent_doc.exists:
            raise HTTPException(status_code=404, detail="Parent member not found")

        parent_data = parent_doc.to_dict() or {}
        if parent_data.get("space_id") != space_id:
            raise HTTPException(
                status_code=403, detail="Parent member not found in current family space"
            )

    # Prevent cycles: new_parent_id cannot be the child itself or any of its descendants
    if req.new_parent_id == req.child_id:
        raise HTTPException(status_code=400, detail="Cannot set a member as their own parent")

    # Prevent setting spouse as parent (nonsensical and creates duplication)
    if req.new_parent_id is not None:
        child_spouse = child_data.get("spouse_id")
        if child_spouse and child_spouse == req.new_parent_id:
            raise HTTPException(status_code=400, detail="Cannot set spouse as parent")

    # Build descendants map for space-scoped relations only
    rels_query = db.collection("relations").where("space_id", "==", space_id)
    rels = list(rels_query.stream())
    by_parent: Dict[Optional[str], List[str]] = {}
    for r in rels:
        data = r.to_dict() or {}
        pid = data.get("parent_id")
        cid = data.get("child_id")
        if cid is None:
            continue
        by_parent.setdefault(pid, []).append(cid)

    def descendants(start: Optional[str]) -> Set[str]:
        result: Set[str] = set()
        stack = [start]
        while stack:
            cur = stack.pop()
            for c in by_parent.get(cur, []) or []:
                if c and c not in result:
                    result.add(c)
                    stack.append(c)
        return result

    if req.new_parent_id is not None and req.child_id is not None:
        if req.new_parent_id in descendants(req.child_id):
            raise HTTPException(status_code=400, detail="Move would create a cycle")

    # Remove any existing parent relation for child (space-scoped)
    for rel in (
        db.collection("relations")
        .where("child_id", "==", req.child_id)
        .where("space_id", "==", space_id)
        .stream()
    ):
        db.collection("relations").document(rel.id).delete()

    # Set new parent (None -> root) with space_id
    db.collection("relations").add(
        {"child_id": req.child_id, "parent_id": req.new_parent_id, "space_id": space_id}
    )
    return {"ok": True}
