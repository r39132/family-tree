"""Tests for app/models.py validation to increase coverage."""

import pytest
from pydantic import ValidationError

from app.models import CreateMember, Member


def test_member_invalid_first_name():
    """Test Member with invalid first_name characters."""
    with pytest.raises(ValidationError) as exc_info:
        Member(
            id="test123",
            first_name="John123",  # Contains numbers
            last_name="Doe",
            dob="1990-01-01",
        )

    error_details = exc_info.value.errors()
    assert any("first_name may only contain letters and -" in str(error) for error in error_details)


def test_member_invalid_last_name():
    """Test Member with invalid last_name characters."""
    with pytest.raises(ValidationError) as exc_info:
        Member(
            id="test123",
            first_name="John",
            last_name="Doe@123",  # Contains special characters
            dob="1990-01-01",
        )

    error_details = exc_info.value.errors()
    assert any("last_name may only contain letters and -" in str(error) for error in error_details)


def test_member_valid_names_with_hyphens():
    """Test Member with valid hyphenated names."""
    member = Member(
        id="test123", first_name="Mary-Jane", last_name="Smith-Williams", dob="1990-01-01"
    )
    assert member.first_name == "Mary-Jane"
    assert member.last_name == "Smith-Williams"


def test_create_member_empty_first_name():
    """Test CreateMember with empty first_name."""
    with pytest.raises(ValidationError) as exc_info:
        CreateMember(
            first_name="",  # Empty string
            last_name="Doe",
            dob="1990-01-01",
        )

    error_details = exc_info.value.errors()
    assert any("first_name is required" in str(error) for error in error_details)


def test_create_member_empty_last_name():
    """Test CreateMember with empty last_name."""
    with pytest.raises(ValidationError) as exc_info:
        CreateMember(
            first_name="John",
            last_name="",  # Empty string
            dob="1990-01-01",
        )

    error_details = exc_info.value.errors()
    assert any("last_name is required" in str(error) for error in error_details)


def test_create_member_empty_dob():
    """Test CreateMember with empty dob."""
    with pytest.raises(ValidationError) as exc_info:
        CreateMember(
            first_name="John",
            last_name="Doe",
            dob="",  # Empty string
        )

    error_details = exc_info.value.errors()
    assert any("dob is required" in str(error) for error in error_details)


def test_create_member_invalid_first_name_characters():
    """Test CreateMember with invalid first_name characters."""
    with pytest.raises(ValidationError) as exc_info:
        CreateMember(
            first_name="John123",  # Contains numbers
            last_name="Doe",
            dob="1990-01-01",
        )

    error_details = exc_info.value.errors()
    assert any("first_name may only contain letters and -" in str(error) for error in error_details)


def test_create_member_invalid_last_name_characters():
    """Test CreateMember with invalid last_name characters."""
    with pytest.raises(ValidationError) as exc_info:
        CreateMember(
            first_name="John",
            last_name="Doe$",  # Contains special character
            dob="1990-01-01",
        )

    error_details = exc_info.value.errors()
    assert any("last_name may only contain letters and -" in str(error) for error in error_details)


def test_empty_to_none_conversion():
    """Test that empty strings are converted to None for optional fields."""
    # This tests the _empty_to_none_req validator
    member = CreateMember(
        first_name="John",
        last_name="Doe",
        dob="1990-01-01",
        nick_name="   ",  # Whitespace only should convert to None
        middle_name="",  # Empty string should convert to None
    )
    assert member.nick_name is None
    assert member.middle_name is None
