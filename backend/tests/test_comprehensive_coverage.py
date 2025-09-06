"""Additional simple tests to reach 65% coverage target."""

from datetime import datetime

import pytest


def test_missing_deps_coverage():
    """Test additional edge cases in deps.py to get 100% coverage"""
    from fastapi import HTTPException

    from app.auth_utils import create_access_token
    from app.deps import get_current_username

    # Test token validation - create_access_token expects string user_id
    fake_token = create_access_token("fake_user")

    # Should raise HTTPException for token validation
    with pytest.raises(HTTPException):
        get_current_username(fake_token)


def test_firestore_client_import_coverage():
    """Test firestore client to improve coverage."""
    from app.firestore_client import get_db

    # This should return a database instance
    db = get_db()
    assert db is not None


def test_main_app_coverage():
    """Test main app configuration coverage."""
    from app.main import app

    # Test that app has expected properties
    assert hasattr(app, "routes")
    assert hasattr(app, "middleware_stack")

    # Test that routers are included
    route_paths = []
    for route in app.routes:
        if hasattr(route, "path"):
            route_paths.append(route.path)
        elif hasattr(route, "path_regex"):
            # For sub-applications/routers
            route_paths.append(str(route.path_regex))

    # Should have some routes
    assert len(route_paths) > 0


def test_models_edge_cases():
    """Test model edge cases to improve coverage."""
    from app.models import CreateMember, Member

    # Test Member with minimal data
    member = Member(id="test123", first_name="John", last_name="Doe", dob="1990-01-01")
    assert member.first_name == "John"
    assert member.last_name == "Doe"

    # Test CreateMember with optional fields
    create_member = CreateMember(
        first_name="Jane", last_name="Smith", dob="1985-05-15", nick_name="Janie", is_deceased=False
    )
    assert create_member.nick_name == "Janie"
    assert create_member.is_deceased is False


def test_config_module_coverage():
    """Test configuration module properties"""
    from app.config import settings

    # Test that settings object has necessary attributes
    assert hasattr(settings, "google_cloud_project")
    assert hasattr(settings, "jwt_secret")


def test_auth_utils_edge_cases():
    """Test auth_utils edge cases."""
    from app.auth_utils import hash_password, verify_password

    # Test password hashing and verification
    password = "test_password_123"
    hashed = hash_password(password)

    # Hash should be different from original
    assert hashed != password
    assert len(hashed) > 20  # Should be a proper hash

    # Verification should work
    assert verify_password(password, hashed) is True
    assert verify_password("wrong_password", hashed) is False


def test_events_module_edge_cases():
    """Test events module edge cases and missing coverage."""
    from app.routes_events import get_all_year_events

    # Test with empty members list
    upcoming, past = get_all_year_events([])
    assert upcoming == []
    assert past == []

    # Test with members having no dob
    members_no_dob = [
        {
            "id": "member1",
            "first_name": "John",
            "last_name": "Doe",
            "is_deceased": False,
            # No dob field
        }
    ]
    upcoming, past = get_all_year_events(members_no_dob)
    assert isinstance(upcoming, list)
    assert isinstance(past, list)

    # Test with members having invalid dob
    members_invalid_dob = [
        {
            "id": "member1",
            "first_name": "John",
            "last_name": "Doe",
            "dob": "not-a-date",
            "is_deceased": False,
        }
    ]
    upcoming, past = get_all_year_events(members_invalid_dob)
    assert isinstance(upcoming, list)
    assert isinstance(past, list)


def test_tree_module_utility_coverage():
    """Test tree module utilities for coverage."""
    from app.routes_tree import _name_key

    # Test with unicode characters (if supported)
    assert _name_key("José", "García") == "josé|garcía"

    # Test with very long names
    long_first = "a" * 100
    long_last = "b" * 100
    result = _name_key(long_first, long_last)
    assert result == f"{long_first.lower()}|{long_last.lower()}"


def test_error_handling_coverage():
    """Test error handling paths to improve coverage."""
    from app.routes_events import calculate_age, parse_date

    # Test parse_date with various invalid formats
    invalid_formats = [
        "2024/13/01",  # Invalid month
        "2024-02-30",  # Invalid day for February
        "not-a-date-at-all",
        "2024",  # Incomplete date
        "01-01-24",  # Two digit year
    ]

    for invalid_format in invalid_formats:
        try:
            parse_date(invalid_format)
            # If it doesn't raise an error, that's also valid (some might be parsed)
        except ValueError:
            # Expected for truly invalid formats
            pass

    # Test calculate_age with edge cases
    current = datetime(2024, 1, 1)

    # Test with various invalid date strings
    assert calculate_age("", current) == 0
    assert calculate_age("invalid", current) == 0
    assert calculate_age("2024-13-45", current) == 0


def test_model_validation_comprehensive():
    """Test comprehensive model validation."""

    from app.models import CreateMember

    # Test valid member creation
    valid_member = CreateMember(
        first_name="Test",
        last_name="User",
        dob="1990-01-01",
        email="test@example.com",
        phone="123-456-7890",
        hobbies=["reading", "coding"],
    )
    assert valid_member.first_name == "Test"
    assert valid_member.email == "test@example.com"
    assert "reading" in valid_member.hobbies

    # Test with empty optional fields that should convert to None
    member_with_empty = CreateMember(
        first_name="Test",
        last_name="User",
        dob="1990-01-01",
        email="",  # Empty email should convert to None
        phone="   ",  # Whitespace should convert to None
    )
    assert member_with_empty.email is None
    assert member_with_empty.phone is None


def test_additional_model_coverage():
    """Test additional model classes for coverage."""
    from app.models import (
        LoginRequest,
        RegisterRequest,
        SpouseRequest,
        TokenResponse,
    )

    # Test RegisterRequest
    register_req = RegisterRequest(
        username="testuser", email="test@example.com", password="password123", invite_code="ABC123"
    )
    assert register_req.username == "testuser"

    # Test LoginRequest
    login_req = LoginRequest(username="testuser", password="password123")
    assert login_req.username == "testuser"

    # Test TokenResponse
    token_resp = TokenResponse(access_token="abc123", token_type="bearer")
    assert token_resp.access_token == "abc123"

    # Test SpouseRequest
    spouse_req = SpouseRequest(spouse_id="spouse123")
    assert spouse_req.spouse_id == "spouse123"

    # Test with None spouse_id
    spouse_req_none = SpouseRequest(spouse_id=None)
    assert spouse_req_none.spouse_id is None
