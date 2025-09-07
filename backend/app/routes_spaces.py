from typing import List

from fastapi import APIRouter, Depends, HTTPException

from .firestore_client import get_db
from .models import FamilySpace, FamilySpaceCreate
from .routes_admin import require_admin
from .utils.time import to_iso_string, utc_now

router = APIRouter(prefix="/spaces", tags=["spaces"])


@router.get("", response_model=List[FamilySpace])
def list_spaces():
    """List all available family spaces"""
    db = get_db()
    spaces = []
    for doc in db.collection("family_spaces").stream():
        data = doc.to_dict()
        spaces.append(
            FamilySpace(
                id=doc.id,
                name=data.get("name", ""),
                description=data.get("description"),
                created_at=data.get("created_at"),
                created_by=data.get("created_by"),
            )
        )
    return sorted(spaces, key=lambda x: x.name.lower())


@router.post("", response_model=FamilySpace)
def create_space(space_data: FamilySpaceCreate, current_user: str = Depends(require_admin)):
    """Create a new family space (admin only)"""
    db = get_db()

    # Check if space already exists
    space_ref = db.collection("family_spaces").document(space_data.id)
    if space_ref.get().exists:
        raise HTTPException(status_code=400, detail="Family space already exists")

    # Create the space
    space_doc = {
        "name": space_data.name,
        "description": space_data.description,
        "created_at": to_iso_string(utc_now()),
        "created_by": current_user,
    }

    space_ref.set(space_doc)

    return FamilySpace(
        id=space_data.id,
        name=space_data.name,
        description=space_data.description,
        created_at=space_doc["created_at"],
        created_by=current_user,
    )


@router.get("/{space_id}", response_model=FamilySpace)
def get_space(space_id: str):
    """Get a specific family space"""
    db = get_db()
    space_ref = db.collection("family_spaces").document(space_id)
    space_doc = space_ref.get()

    if not space_doc.exists:
        raise HTTPException(status_code=404, detail="Family space not found")

    data = space_doc.to_dict()
    return FamilySpace(
        id=space_id,
        name=data.get("name", ""),
        description=data.get("description"),
        created_at=data.get("created_at"),
        created_by=data.get("created_by"),
    )


@router.delete("/{space_id}")
def delete_space(space_id: str, current_user: str = Depends(require_admin)):
    """Delete a family space (admin only)"""
    db = get_db()
    space_ref = db.collection("family_spaces").document(space_id)

    if not space_ref.get().exists:
        raise HTTPException(status_code=404, detail="Family space not found")

    # TODO: Consider adding checks for existing users/members in this space
    # For now, allow deletion but could add safeguards later

    space_ref.delete()
    return {"message": "Family space deleted successfully"}


def get_user_space(username: str) -> str:
    """Get the current space for a user. Returns 'demo' as fallback."""
    db = get_db()
    user_ref = db.collection("users").document(username)
    user_doc = user_ref.get()

    if not user_doc.exists:
        return "demo"  # Default fallback

    data = user_doc.to_dict()
    return data.get("current_space", "demo")


def set_user_space(username: str, space_id: str):
    """Set the current space for a user"""
    db = get_db()
    user_ref = db.collection("users").document(username)
    user_ref.update({"current_space": space_id})


def ensure_default_spaces():
    """Ensure the default family spaces exist"""
    db = get_db()

    default_spaces = [
        {"id": "demo", "name": "Demo", "description": "Demo family space for testing"},
        {"id": "karunakaran", "name": "Karunakaran", "description": "Karunakaran family"},
        {"id": "anand", "name": "Anand", "description": "Anand family"},
        {"id": "kullatira", "name": "Kullatira", "description": "Kullatira family"},
    ]

    for space in default_spaces:
        space_ref = db.collection("family_spaces").document(space["id"])
        if not space_ref.get().exists:
            space_ref.set(
                {
                    "name": space["name"],
                    "description": space["description"],
                    "created_at": to_iso_string(utc_now()),
                    "created_by": "system",
                }
            )
