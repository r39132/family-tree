import base64
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, field_validator

from .deps import get_current_username
from .firestore_client import get_db

router = APIRouter(prefix="/user", tags=["user"])


class ProfileResponse(BaseModel):
    username: str
    email: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    profile_photo_data_url: Optional[str] = None
    roles: Optional[list[str]] = None


class ProfileUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None

    @field_validator("first_name", "last_name")
    @classmethod
    def _clean_names(cls, v: Optional[str]):
        if v is None:
            return v
        v = v.strip()
        if len(v) == 0:
            raise ValueError("must not be empty")
        if len(v) > 50:
            raise ValueError("too long (max 50)")
        return v


class PhotoUpdate(BaseModel):
    image_data_url: str

    @field_validator("image_data_url")
    @classmethod
    def _validate_data_url(cls, v: str):
        v = v.strip()
        # Basic validation
        if not (
            v.startswith("data:image/png;base64,")
            or v.startswith("data:image/jpeg;base64,")
            or v.startswith("data:image/jpg;base64,")
        ):
            raise ValueError("image_data_url must be a PNG or JPEG data URL")
        # Enforce 1MB (decoded) limit
        try:
            b64 = v.split(",", 1)[1]
        except IndexError:
            raise ValueError("invalid data URL format")
        try:
            raw = base64.b64decode(b64, validate=True)
        except Exception:
            raise ValueError("invalid base64 image data")
        if len(raw) > 262_144:  # 256KB
            raise ValueError("image too large; max 256KB")
        return v


@router.get("/profile", response_model=ProfileResponse)
def get_profile(current_user: str = Depends(get_current_username)):
    db = get_db()
    doc = db.collection("users").document(current_user).get()
    if not doc.exists:
        raise HTTPException(status_code=404, detail="User not found")
    data = doc.to_dict() or {}
    return ProfileResponse(
        username=current_user,
        email=data.get("email"),
        first_name=data.get("first_name"),
        last_name=data.get("last_name"),
        profile_photo_data_url=data.get("profile_photo_data_url"),
        roles=data.get("roles", []),
    )


@router.put("/profile", response_model=ProfileResponse)
def update_profile(update: ProfileUpdate, current_user: str = Depends(get_current_username)):
    db = get_db()
    ref = db.collection("users").document(current_user)
    doc = ref.get()
    if not doc.exists:
        raise HTTPException(status_code=404, detail="User not found")

    payload = {}
    if update.first_name is not None:
        payload["first_name"] = update.first_name
    if update.last_name is not None:
        payload["last_name"] = update.last_name

    if payload:
        ref.update(payload)

    # Return updated
    new_doc = ref.get().to_dict() or {}
    return ProfileResponse(
        username=current_user,
        email=new_doc.get("email"),
        first_name=new_doc.get("first_name"),
        last_name=new_doc.get("last_name"),
        profile_photo_data_url=new_doc.get("profile_photo_data_url"),
        roles=new_doc.get("roles", []),
    )


@router.post("/profile/photo", response_model=ProfileResponse)
def upload_profile_photo(update: PhotoUpdate, current_user: str = Depends(get_current_username)):
    db = get_db()
    ref = db.collection("users").document(current_user)
    doc = ref.get()
    if not doc.exists:
        raise HTTPException(status_code=404, detail="User not found")

    # Store data URL directly (already size-limited)
    ref.update({"profile_photo_data_url": update.image_data_url})

    new_doc = ref.get().to_dict() or {}
    return ProfileResponse(
        username=current_user,
        email=new_doc.get("email"),
        first_name=new_doc.get("first_name"),
        last_name=new_doc.get("last_name"),
        profile_photo_data_url=new_doc.get("profile_photo_data_url"),
        roles=new_doc.get("roles", []),
    )
