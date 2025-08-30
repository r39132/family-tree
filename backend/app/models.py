import re
from typing import List, Optional

from pydantic import BaseModel, EmailStr, Field, field_validator


class RegisterRequest(BaseModel):
    invite_code: str
    username: str
    email: EmailStr
    password: str


class LoginRequest(BaseModel):
    username: str
    password: str


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
    birth_location: Optional[str] = None
    residence_location: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    hobbies: List[str] = Field(default_factory=list)

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
    residence_location: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    hobbies: List[str] = Field(default_factory=list)

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

    @field_validator(
        "email",
        "nick_name",
        "middle_name",
        "birth_location",
        "residence_location",
        "phone",
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
    birth_location: Optional[str] = None
    residence_location: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    hobbies: Optional[List[str]] = None
