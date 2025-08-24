from app.config import Settings
from app.models import *
import pytest
from datetime import datetime


def test_settings_defaults():
    """Test settings have reasonable defaults"""
    settings = Settings()
    assert settings.app_name == "Family Tree API"
    assert settings.app_version == "0.1.0"  # Correct version from pyproject.toml
    assert settings.jwt_secret is not None  # Use correct field name
    assert settings.jwt_alg == "HS256"
    assert settings.access_token_expire_minutes == 60
    assert settings.require_invite is True


def test_register_request_model():
    """Test RegisterRequest model validation"""
    req = RegisterRequest(
        username="testuser",
        email="test@example.com",
        password="password123",
        confirm_password="password123",
        invite_code="abc123"
    )
    assert req.username == "testuser"
    assert req.email == "test@example.com"


def test_login_request_model():
    """Test LoginRequest model"""
    req = LoginRequest(username="testuser", password="password123")
    assert req.username == "testuser"
    assert req.password == "password123"


def test_forgot_request_model():
    """Test ForgotRequest model"""
    req = ForgotRequest(username="testuser", email="test@example.com")
    assert req.username == "testuser"
    assert req.email == "test@example.com"


def test_reset_request_model():
    """Test ResetRequest model"""
    req = ResetRequest(
        username="testuser",
        token="abc123",
        new_password="newpass123",
        confirm_password="newpass123"
    )
    assert req.username == "testuser"
    assert req.token == "abc123"


def test_token_response_model():
    """Test TokenResponse model"""
    resp = TokenResponse(access_token="abc123", token_type="bearer")
    assert resp.access_token == "abc123"
    assert resp.token_type == "bearer"


def test_member_model():
    """Test Member model"""
    member = Member(
        id="123",
        first_name="John",
        last_name="Doe",
        dob="01/15/1990",
        email="john@example.com"
    )
    assert member.id == "123"
    assert member.first_name == "John"
    assert member.last_name == "Doe"


def test_create_member_model():
    """Test CreateMember model"""
    member = CreateMember(
        first_name="Jane",
        last_name="Smith",
        dob="05/20/1985"
    )
    assert member.first_name == "Jane"
    assert member.last_name == "Smith"
    assert member.dob == "05/20/1985"


def test_move_request_model():
    """Test MoveRequest model"""
    req = MoveRequest(child_id="child123", new_parent_id="parent456")
    assert req.child_id == "child123"
    assert req.new_parent_id == "parent456"


def test_move_request_null_parent():
    """Test MoveRequest with null parent (root)"""
    req = MoveRequest(child_id="child123", new_parent_id=None)
    assert req.child_id == "child123"
    assert req.new_parent_id is None


def test_spouse_request_model():
    """Test SpouseRequest model"""
    req = SpouseRequest(spouse_id="spouse123")
    assert req.spouse_id == "spouse123"


def test_spouse_request_null():
    """Test SpouseRequest with null spouse (unlink)"""
    req = SpouseRequest(spouse_id=None)
    assert req.spouse_id is None


def test_member_optional_fields():
    """Test Member model with optional fields"""
    member = Member(
        id="123",
        first_name="John",
        last_name="Doe",
        dob="01/15/1990",
        middle_name="Michael",
        birth_location="New York",
        residence_location="California",
        email="john@example.com",
        phone="555-1234",
        hobbies=["reading", "hiking"],
        spouse_id="spouse123",
        is_deceased=True
    )
    assert member.middle_name == "Michael"
    assert member.birth_location == "New York"
    assert member.hobbies == ["reading", "hiking"]
    assert member.spouse_id == "spouse123"
    assert member.is_deceased is True
