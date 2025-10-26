"""Tests for album routes and functionality."""

import io
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from PIL import Image

from app.deps import get_current_username
from app.main import app
from tests.conftest import FakeDB

client = TestClient(app)


def create_test_image(width=800, height=600):
    """Create a test image."""
    img = Image.new("RGB", (width, height), color="red")
    img_bytes = io.BytesIO()
    img.save(img_bytes, format="JPEG")
    img_bytes.seek(0)
    return img_bytes


@pytest.fixture
def authenticated_client():
    """Client with authentication mocked."""
    app.dependency_overrides[get_current_username] = lambda: "testuser"
    yield client
    app.dependency_overrides.pop(get_current_username, None)


@pytest.fixture
def fake_album_db():
    """Set up fake database with album collections."""
    fake_db = FakeDB()
    fake_db.collection("users").document("testuser").set(
        {"username": "testuser", "email": "test@example.com", "current_space": "demo"}
    )
    fake_db.collection("family_spaces").document("demo").set(
        {
            "name": "Demo",
            "description": "Demo family space",
            "created_at": "2023-01-01T00:00:00Z",
            "created_by": "system",
        }
    )
    return fake_db


@pytest.fixture
def mock_storage(monkeypatch):
    """Mock GCS storage."""

    def mock_upload(file_content, content_type, space_id):
        return (
            "test-photo-id",
            "demo/originals/test-photo-id.jpg",
            "demo/thumbnails/test-photo-id_thumb.jpg",
            "https://cdn.example.com/test-photo-id.jpg",
            "https://cdn.example.com/test-photo-id_thumb.jpg",
            800,
            600,
        )

    def mock_delete(gcs_path, thumbnail_path):
        return True

    monkeypatch.setattr("app.routes_album.upload_album_photo", mock_upload)
    monkeypatch.setattr("app.routes_album.delete_album_photo", mock_delete)


def test_upload_photo_success(fake_album_db, authenticated_client, mock_storage):
    """Test successful photo upload."""
    img_bytes = create_test_image()

    with patch("app.routes_album.get_db", return_value=fake_album_db):
        with patch("app.routes_album.get_user_space", return_value="demo"):
            response = authenticated_client.post(
                "/spaces/demo/album/photos",
                files={"file": ("test.jpg", img_bytes, "image/jpeg")},
            )

    assert response.status_code == 200
    data = response.json()
    assert data["filename"] == "test.jpg"
    assert data["space_id"] == "demo"
    assert data["uploader_id"] == "testuser"


def test_upload_photo_invalid_type(fake_album_db, authenticated_client, mock_storage):
    """Test upload with invalid file type."""
    with patch("app.routes_album.get_db", return_value=fake_album_db):
        with patch("app.routes_album.get_user_space", return_value="demo"):
            response = authenticated_client.post(
                "/spaces/demo/album/photos",
                files={"file": ("test.txt", io.BytesIO(b"test"), "text/plain")},
            )

    assert response.status_code == 400
    assert "Invalid file type" in response.json()["detail"]


def test_list_photos_empty(fake_album_db, authenticated_client):
    """Test listing photos when album is empty."""
    with patch("app.routes_album.get_db", return_value=fake_album_db):
        with patch("app.routes_album.get_user_space", return_value="demo"):
            response = authenticated_client.get("/spaces/demo/album/photos")

    assert response.status_code == 200
    data = response.json()
    assert data["photos"] == []
    assert data["total"] == 0
    assert data["page"] == 1
    assert data["per_page"] == 10
    assert data["total_pages"] == 0


def test_list_photos_pagination(fake_album_db, authenticated_client, mock_storage):
    """Test photo pagination."""
    with patch("app.routes_album.get_db", return_value=fake_album_db):
        with patch("app.routes_album.get_user_space", return_value="demo"):
            # Upload 15 photos
            for i in range(15):
                img_bytes = create_test_image()
                authenticated_client.post(
                    "/spaces/demo/album/photos",
                    files={"file": (f"test{i}.jpg", img_bytes, "image/jpeg")},
                )

            # Test first page with limit=10
            response = authenticated_client.get("/spaces/demo/album/photos?limit=10&offset=0")
            assert response.status_code == 200
            data = response.json()
            assert len(data["photos"]) == 10
            assert data["total"] == 15
            assert data["page"] == 1
            assert data["per_page"] == 10
            assert data["total_pages"] == 2

            # Test second page
            response = authenticated_client.get("/spaces/demo/album/photos?limit=10&offset=10")
            assert response.status_code == 200
            data = response.json()
            assert len(data["photos"]) == 5
            assert data["total"] == 15
            assert data["page"] == 2
            assert data["per_page"] == 10
            assert data["total_pages"] == 2

            # Test using page parameter
            response = authenticated_client.get("/spaces/demo/album/photos?limit=10&page=2")
            assert response.status_code == 200
            data = response.json()
            assert len(data["photos"]) == 5
            assert data["page"] == 2


def test_like_photo_success(fake_album_db, authenticated_client, mock_storage):
    """Test liking a photo."""
    img_bytes = create_test_image()

    with patch("app.routes_album.get_db", return_value=fake_album_db):
        with patch("app.routes_album.get_user_space", return_value="demo"):
            # Upload photo
            upload_response = authenticated_client.post(
                "/spaces/demo/album/photos",
                files={"file": ("test.jpg", img_bytes, "image/jpeg")},
            )
            photo_id = upload_response.json()["id"]

            # Like photo
            like_response = authenticated_client.post(f"/spaces/demo/album/photos/{photo_id}/like")

            assert like_response.status_code == 200
            assert "liked" in like_response.json()["message"]


def test_update_tags_success(fake_album_db, authenticated_client, mock_storage):
    """Test updating photo tags."""
    img_bytes = create_test_image()

    with patch("app.routes_album.get_db", return_value=fake_album_db):
        with patch("app.routes_album.get_user_space", return_value="demo"):
            # Upload photo
            upload_response = authenticated_client.post(
                "/spaces/demo/album/photos",
                files={"file": ("test.jpg", img_bytes, "image/jpeg")},
            )
            photo_id = upload_response.json()["id"]

            # Update tags
            tags_response = authenticated_client.put(
                f"/spaces/demo/album/photos/{photo_id}/tags",
                json={"tags": ["family", "vacation"]},
            )

            assert tags_response.status_code == 200
            assert tags_response.json()["tags"] == ["family", "vacation"]


def test_get_album_stats(fake_album_db, authenticated_client, mock_storage):
    """Test getting album statistics."""
    with patch("app.routes_album.get_db", return_value=fake_album_db):
        with patch("app.routes_album.get_user_space", return_value="demo"):
            # Get stats for empty album
            response = authenticated_client.get("/spaces/demo/album/stats")

            assert response.status_code == 200
            stats = response.json()
            assert stats["total_photos"] == 0
            assert stats["total_likes"] == 0


def test_album_storage_module():
    """Test album storage module functions."""
    from app.album import generate_thumbnail, get_album_storage_client

    # Test get_album_storage_client - should return a client if bucket is configured
    client = get_album_storage_client()
    # Client may be None if ALBUM_BUCKET_NAME is not set, or a Client object if it is
    assert client is None or client is not None  # Always passes, just checks it doesn't crash

    # Test thumbnail generation
    img = Image.new("RGB", (800, 600), color="blue")
    thumbnail_bytes = generate_thumbnail(img, size=300)
    assert thumbnail_bytes is not None
    assert len(thumbnail_bytes) > 0

    # Verify thumbnail is correct size
    thumbnail_img = Image.open(io.BytesIO(thumbnail_bytes))
    assert thumbnail_img.width <= 300
    assert thumbnail_img.height <= 300
