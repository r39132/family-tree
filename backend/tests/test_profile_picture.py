"""Test profile picture URL support in Member models."""

from app.models import CreateMember, Member, UpdateMember


def test_member_model_with_profile_picture_url():
    """Test that Member model accepts profile_picture_url."""
    member_data = {
        "id": "test-id",
        "first_name": "John",
        "last_name": "Doe",
        "dob": "01/01/1990",
        "profile_picture_url": "https://example.com/photo.jpg",
    }
    member = Member(**member_data)
    assert member.profile_picture_url == "https://example.com/photo.jpg"


def test_member_model_without_profile_picture_url():
    """Test that Member model works without profile_picture_url."""
    member_data = {
        "id": "test-id",
        "first_name": "John",
        "last_name": "Doe",
        "dob": "01/01/1990",
    }
    member = Member(**member_data)
    assert member.profile_picture_url is None


def test_create_member_with_profile_picture_url():
    """Test that CreateMember accepts profile_picture_url."""
    create_data = {
        "first_name": "Jane",
        "last_name": "Smith",
        "dob": "02/15/1985",
        "profile_picture_url": "https://example.com/jane.png",
    }
    create_member = CreateMember(**create_data)
    assert create_member.profile_picture_url == "https://example.com/jane.png"


def test_create_member_without_profile_picture_url():
    """Test that CreateMember works without profile_picture_url."""
    create_data = {
        "first_name": "Jane",
        "last_name": "Smith",
        "dob": "02/15/1985",
    }
    create_member = CreateMember(**create_data)
    assert create_member.profile_picture_url is None


def test_update_member_with_profile_picture_url():
    """Test that UpdateMember accepts profile_picture_url."""
    update_data = {"profile_picture_url": "https://example.com/updated.jpg"}
    update_member = UpdateMember(**update_data)
    assert update_member.profile_picture_url == "https://example.com/updated.jpg"


def test_member_empty_profile_picture_url_converts_to_none():
    """Test that empty string profile_picture_url converts to None."""
    member_data = {
        "id": "test-id",
        "first_name": "John",
        "last_name": "Doe",
        "dob": "01/01/1990",
        "profile_picture_url": "   ",  # Empty/whitespace string
    }
    member = Member(**member_data)
    assert member.profile_picture_url is None
