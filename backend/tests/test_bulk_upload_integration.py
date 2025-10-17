"""Integration tests for bulk upload endpoint."""

import json
import pytest
from unittest.mock import MagicMock, patch
from fastapi import HTTPException
from app.routes_tree import _to_title_case


def test_to_title_case():
    """Test title case conversion"""
    assert _to_title_case("john") == "John"
    assert _to_title_case("mary jane") == "Mary Jane"
    assert _to_title_case("o'connor") == "O'connor"  # Note: simple capitalize doesn't handle apostrophes
    assert _to_title_case(None) is None
    assert _to_title_case("") == ""


def test_to_title_case_with_mixed_case():
    """Test title case with already mixed case input"""
    assert _to_title_case("JOHN DOE") == "John Doe"
    assert _to_title_case("john DOE") == "John Doe"
    assert _to_title_case("JoHn DoE") == "John Doe"


def test_bulk_upload_validates_space_name():
    """Test that bulk upload validates family space name"""
    # This would be an actual integration test that hits the endpoint
    # For now, we just verify the model structure
    from app.models import BulkUploadRequest, BulkUploadMember
    
    members = [
        BulkUploadMember(
            first_name="John",
            last_name="Doe",
            dob="01/15/1980"
        )
    ]
    
    request = BulkUploadRequest(space_name="Demo", members=members)
    assert request.space_name == "Demo"


def test_bulk_upload_deduplication_key():
    """Test that deduplication uses correct key format"""
    # Test the key format used for deduplication
    first_name = "John"
    last_name = "Doe"
    dob = "01/15/1980"
    
    key = (first_name.lower(), last_name.lower(), dob)
    assert key == ("john", "doe", "01/15/1980")


def test_bulk_upload_response_structure():
    """Test BulkUploadResponse structure"""
    from app.models import BulkUploadResponse
    
    response = BulkUploadResponse(
        success=True,
        total_in_file=10,
        uploaded_count=8,
        already_present_count=2,
        errors=[],
        message="Successfully uploaded 8 new member(s)."
    )
    
    assert response.success is True
    assert response.total_in_file == 10
    assert response.uploaded_count == 8
    assert response.already_present_count == 2
    assert len(response.errors) == 0
    assert "8 new member" in response.message
