import re
from datetime import datetime, timezone
from typing import List, Optional

from pydantic import BaseModel, EmailStr, Field, ValidationInfo, field_validator

from .utils.time import utc_now


class RegisterRequest(BaseModel):
    invite_code: str
    username: str
    email: EmailStr
    password: str
    space_id: Optional[str] = None  # Selected family space


class LoginRequest(BaseModel):
    username: str
    password: str
    space_id: Optional[str] = None  # Selected family space


class ForgotRequest(BaseModel):
    username: str
    email: EmailStr


class ResetRequest(BaseModel):
    username: str
    new_password: str
    confirm_password: str
    token: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class Member(BaseModel):
    id: Optional[str] = None
    first_name: str
    nick_name: Optional[str] = None
    middle_name: Optional[str] = None
    last_name: str
    dob: Optional[str] = None
    spouse_id: Optional[str] = None
    is_deceased: Optional[bool] = False
    date_of_death: Optional[str] = None
    birth_location: Optional[str] = None
    residence_location: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    hobbies: List[str] = Field(default_factory=list)
    profile_picture_url: Optional[str] = None

    @field_validator("first_name")
    @classmethod
    def _validate_first(cls, v: str):
        if v is None:
            return v
        if not re.fullmatch(r"[A-Za-z-]+", v):
            raise ValueError("first_name may only contain letters and -")
        return v

    @field_validator("last_name")
    @classmethod
    def _validate_last(cls, v: str):
        if v is None:
            return v
        if not re.fullmatch(r"[A-Za-z-]+", v):
            raise ValueError("last_name may only contain letters and -")
        return v

    # Be tolerant on DOB format at the model level; routes derive dob_ts when possible
    @field_validator("dob")
    @classmethod
    def _validate_dob(cls, v: Optional[str]):
        return v

    @field_validator(
        "email",
        "nick_name",
        "middle_name",
        "birth_location",
        "residence_location",
        "phone",
        "profile_picture_url",
        mode="before",
    )
    @classmethod
    def _empty_to_none(cls, v):
        # Convert empty strings to None so optional fields don't fail validation
        if isinstance(v, str) and v.strip() == "":
            return None
        return v


class CreateMember(BaseModel):
    first_name: str
    last_name: str
    dob: str
    nick_name: Optional[str] = None
    spouse_id: Optional[str] = None
    is_deceased: Optional[bool] = False
    middle_name: Optional[str] = None
    birth_location: Optional[str] = None
    date_of_death: Optional[str] = None
    residence_location: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    hobbies: List[str] = Field(default_factory=list)
    profile_picture_url: Optional[str] = None

    @field_validator("first_name")
    @classmethod
    def _validate_first_req(cls, v: str):
        if not v:
            raise ValueError("first_name is required")
        if not re.fullmatch(r"[A-Za-z-]+", v):
            raise ValueError("first_name may only contain letters and -")
        return v

    @field_validator("last_name")
    @classmethod
    def _validate_last_req(cls, v: str):
        if not v:
            raise ValueError("last_name is required")
        if not re.fullmatch(r"[A-Za-z-]+", v):
            raise ValueError("last_name may only contain letters and -")
        return v

    @field_validator("dob")
    @classmethod
    def _validate_dob_req(cls, v: str):
        if not v:
            raise ValueError("dob is required")
        # Accept any non-empty string; route will attempt to parse
        return v

    @field_validator("dob", "date_of_death")
    @classmethod
    def _validate_past_date(cls, v: str):
        try:
            date = datetime.strptime(v, "%m/%d/%Y").replace(tzinfo=timezone.utc)
        except Exception:
            return v

        if date > utc_now():
            raise ValueError("This date cannot be in the future")

        return v

    @field_validator("date_of_death")
    @classmethod
    def _validate_date_of_death_future_to_dob(cls, v: str, info: ValidationInfo):
        try:
            dates = [
                datetime.strptime(x, "%m/%d/%Y").replace(tzinfo=timezone.utc)
                for x in [v, info.data["dob"]]
            ]
        except Exception:
            return v

        if dates[0] <= dates[1]:
            raise ValueError("Date of Death must be later than Date of Birth.")

        return v

    @field_validator(
        "email",
        "nick_name",
        "middle_name",
        "birth_location",
        "residence_location",
        "phone",
        "profile_picture_url",
        mode="before",
    )
    @classmethod
    def _empty_to_none_req(cls, v):
        # Convert empty strings to None so optional fields don't fail validation
        if isinstance(v, str) and v.strip() == "":
            return None
        return v


class SpouseRequest(BaseModel):
    spouse_id: Optional[str] = None


class MoveRequest(BaseModel):
    child_id: str
    new_parent_id: Optional[str]  # None -> make root


class RecoverTreeRequest(BaseModel):
    version_id: str


class TreeVersionInfo(BaseModel):
    id: str
    created_at: str
    version: int
    relations_count: int | None = None


class UpdateMember(BaseModel):
    # All fields optional for PATCH semantics
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    dob: Optional[str] = None
    nick_name: Optional[str] = None
    spouse_id: Optional[str] = None
    is_deceased: Optional[bool] = None
    middle_name: Optional[str] = None
    date_of_death: Optional[str] = None
    birth_location: Optional[str] = None
    residence_location: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    hobbies: Optional[List[str]] = None
    profile_picture_url: Optional[str] = None

    @field_validator("dob", "date_of_death")
    @classmethod
    def _validate_past_date_update(cls, v: Optional[str]):
        if v is None or not v.strip():
            return v
        try:
            date = datetime.strptime(v, "%m/%d/%Y").replace(tzinfo=timezone.utc)
        except Exception:
            return v

        if date > utc_now():
            raise ValueError("This date cannot be in the future")

        return v

    @field_validator("date_of_death")
    @classmethod
    def _validate_date_of_death_after_dob_update(cls, v: Optional[str], info: ValidationInfo):
        if v is None or not v.strip():
            return v
        dob = info.data.get("dob")
        if dob is None or not dob.strip():
            return v  # Can't validate relationship if no dob provided
        try:
            dates = [
                datetime.strptime(x, "%m/%d/%Y").replace(tzinfo=timezone.utc) for x in [v, dob]
            ]
        except Exception:
            return v

        if dates[0] <= dates[1]:
            raise ValueError("Date of Death must be later than Date of Birth.")

        return v


class EventNotificationSettings(BaseModel):
    enabled: bool = False
    user_id: str


class FamilyEvent(BaseModel):
    id: str
    member_id: str
    member_name: str
    event_type: str  # "birthday" or "death_anniversary"
    event_date: str  # YYYY-MM-DD format for this year's occurrence
    age_on_date: int
    original_date: str  # Original birth/death date


class EventsResponse(BaseModel):
    upcoming_events: List[FamilyEvent]
    past_events: List[FamilyEvent]
    notification_enabled: bool


class EventNotificationLog(BaseModel):
    """Track individual event notifications to prevent duplicates."""

    id: str  # Unique ID for this notification log entry
    user_id: str
    space_id: str
    member_id: str
    event_type: str  # "birthday" or "death_anniversary"
    event_date: str  # YYYY-MM-DD format for this year's occurrence
    notification_sent_at: str  # ISO timestamp when notification was sent
    created_at: Optional[str] = None  # When this log entry was created


class FamilySpace(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    created_at: Optional[str] = None
    created_by: Optional[str] = None


class FamilySpaceCreate(BaseModel):
    id: str
    name: str
    description: Optional[str] = None

    @field_validator("id")
    @classmethod
    def _validate_id(cls, v: str):
        if not v or not v.strip():
            raise ValueError("ID is required")
        v = v.strip().lower()
        if not re.match(r"^[a-z0-9_-]+$", v):
            raise ValueError(
                "ID must contain only lowercase letters, numbers, hyphens, and underscores"
            )
        if len(v) > 50:
            raise ValueError("ID too long (max 50 characters)")
        return v

    @field_validator("name")
    @classmethod
    def _validate_name(cls, v: str):
        if not v or not v.strip():
            raise ValueError("Name is required")
        v = v.strip()
        if len(v) > 100:
            raise ValueError("Name too long (max 100 characters)")
        return v


class SpaceSelectionRequest(BaseModel):
    space_id: str

    @field_validator("space_id")
    @classmethod
    def _validate_space_id(cls, v: str):
        if not v or not v.strip():
            raise ValueError("Space ID is required")
        return v.strip().lower()


class BulkUploadMember(BaseModel):
    """Model for a single member in bulk upload"""

    first_name: str
    last_name: str
    dob: str
    nick_name: Optional[str] = None
    middle_name: Optional[str] = None
    is_deceased: Optional[bool] = False
    date_of_death: Optional[str] = None
    birth_location: Optional[str] = None
    residence_location: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    hobbies: List[str] = Field(default_factory=list)
    parent_name: Optional[str] = None
    spouse_name: Optional[str] = None


class BulkUploadRequest(BaseModel):
    """Model for bulk upload request"""

    space_name: str
    members: List[BulkUploadMember]


class BulkUploadResponse(BaseModel):
    """Response model for bulk upload"""

    success: bool
    total_in_file: int
    uploaded_count: int
    already_present_count: int
    errors: List[str] = Field(default_factory=list)
    message: Optional[str] = None
