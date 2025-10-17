"""Tests for bulk upload functionality."""

import pytest
from app.models import BulkUploadMember, BulkUploadRequest


def test_bulk_upload_member_model():
    """Test BulkUploadMember model validation"""
    member = BulkUploadMember(
        first_name="John",
        last_name="Doe",
        dob="01/15/1980",
        email="john@example.com",
    )
    assert member.first_name == "John"
    assert member.last_name == "Doe"
    assert member.dob == "01/15/1980"
    assert member.email == "john@example.com"


def test_bulk_upload_request_model():
    """Test BulkUploadRequest model validation"""
    members = [
        BulkUploadMember(
            first_name="John", last_name="Doe", dob="01/15/1980"
        ),
        BulkUploadMember(
            first_name="Jane", last_name="Doe", dob="03/20/1982"
        ),
    ]
    request = BulkUploadRequest(space_name="Demo", members=members)
    assert request.space_name == "Demo"
    assert len(request.members) == 2
    assert request.members[0].first_name == "John"
    assert request.members[1].first_name == "Jane"


def test_bulk_upload_member_with_relationships():
    """Test BulkUploadMember with parent and spouse relationships"""
    member = BulkUploadMember(
        first_name="John",
        last_name="Doe",
        dob="01/15/1980",
        parent_name="Jane Doe",
        spouse_name="Mary Doe",
    )
    assert member.parent_name == "Jane Doe"
    assert member.spouse_name == "Mary Doe"


def test_bulk_upload_member_with_optional_fields():
    """Test BulkUploadMember with all optional fields"""
    member = BulkUploadMember(
        first_name="John",
        last_name="Doe",
        dob="01/15/1980",
        nick_name="Johnny",
        middle_name="Michael",
        birth_location="New York",
        residence_location="California",
        email="john@example.com",
        phone="555-1234",
        hobbies=["Reading", "Hiking"],
        is_deceased=False,
    )
    assert member.nick_name == "Johnny"
    assert member.middle_name == "Michael"
    assert member.birth_location == "New York"
    assert member.residence_location == "California"
    assert member.phone == "555-1234"
    assert len(member.hobbies) == 2
    assert member.is_deceased is False
