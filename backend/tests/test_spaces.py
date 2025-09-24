"""Tests for family spaces functionality."""

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app.deps import get_current_username
from app.main import app
from app.routes_spaces import ensure_default_spaces, get_user_space, set_user_space
from tests.conftest import FakeDB


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def unauthenticated_client(client):
    """Client without authentication - should get 401/403 for admin endpoints."""
    # Make sure no authentication is set up
    app.dependency_overrides.pop(get_current_username, None)
    from app.routes_admin import require_admin

    app.dependency_overrides.pop(require_admin, None)
    yield client


@pytest.fixture
def authenticated_admin_client(client):
    """Client with admin authentication mocked."""
    # Store original overrides if any
    orig_user = app.dependency_overrides.get(get_current_username)

    # Override to return admin user
    app.dependency_overrides[get_current_username] = lambda: "admin_user"

    # Also need to mock require_admin dependency since some endpoints use it directly
    from app.routes_admin import require_admin

    orig_admin = app.dependency_overrides.get(require_admin)
    app.dependency_overrides[require_admin] = lambda: "admin_user"

    yield client

    # Restore original overrides
    if orig_user:
        app.dependency_overrides[get_current_username] = orig_user
    else:
        app.dependency_overrides.pop(get_current_username, None)

    if orig_admin:
        app.dependency_overrides[require_admin] = orig_admin
    else:
        app.dependency_overrides.pop(require_admin, None)


@pytest.fixture
def fake_spaces_db():
    """Set up fake database with spaces data."""
    fake_db = FakeDB()

    # Create some test family spaces
    fake_db.collection("family_spaces").document("demo").set(
        {
            "name": "Demo Family",
            "description": "Demo family space",
            "created_at": "2023-01-01T00:00:00Z",
            "created_by": "system",
        }
    )

    fake_db.collection("family_spaces").document("smith_family").set(
        {
            "name": "Smith Family",
            "description": "The Smith family tree",
            "created_at": "2023-01-02T00:00:00Z",
            "created_by": "admin_user",
        }
    )

    # Create test users
    fake_db.collection("users").document("test_user").set(
        {"current_space": "demo", "username": "test_user"}
    )

    fake_db.collection("users").document("admin_user").set(
        {"current_space": "smith_family", "username": "admin_user"}
    )

    return fake_db


class TestSpacesList:
    """Test listing family spaces."""

    def test_list_spaces_success(self, client, fake_spaces_db):
        """Test successful listing of family spaces."""
        with patch("app.routes_spaces.get_db", return_value=fake_spaces_db):
            response = client.get("/spaces")

        assert response.status_code == 200
        spaces = response.json()
        assert len(spaces) == 2

        # Check spaces are sorted by name
        assert spaces[0]["name"] == "Demo Family"
        assert spaces[1]["name"] == "Smith Family"

        # Verify space structure
        demo_space = spaces[0]
        assert demo_space["id"] == "demo"
        assert demo_space["description"] == "Demo family space"
        assert demo_space["created_by"] == "system"

    def test_list_spaces_empty(self, client):
        """Test listing when no spaces exist."""
        empty_db = FakeDB()

        with patch("app.routes_spaces.get_db", return_value=empty_db):
            response = client.get("/spaces")

        assert response.status_code == 200
        assert response.json() == []


class TestSpacesCreate:
    """Test creating family spaces."""

    def test_create_space_success(self, authenticated_admin_client, fake_spaces_db):
        """Test successful space creation by admin."""
        space_data = {
            "id": "johnson_family",
            "name": "Johnson Family",
            "description": "The Johnson family tree",
        }

        with patch("app.routes_spaces.get_db", return_value=fake_spaces_db):
            response = authenticated_admin_client.post("/spaces", json=space_data)

        assert response.status_code == 200
        created_space = response.json()

        assert created_space["id"] == "johnson_family"
        assert created_space["name"] == "Johnson Family"
        assert created_space["description"] == "The Johnson family tree"
        assert created_space["created_by"] == "admin_user"
        assert "created_at" in created_space

    def test_create_space_duplicate(self, authenticated_admin_client, fake_spaces_db):
        """Test creating space with existing ID fails."""
        space_data = {
            "id": "demo",  # Already exists
            "name": "Another Demo",
            "description": "Another demo space",
        }

        with patch("app.routes_spaces.get_db", return_value=fake_spaces_db):
            response = authenticated_admin_client.post("/spaces", json=space_data)

        assert response.status_code == 400
        assert "already exists" in response.json()["detail"]

    def test_create_space_unauthorized(self, unauthenticated_client, fake_spaces_db):
        """Test creating space without admin access fails."""
        space_data = {
            "id": "unauthorized_space",
            "name": "Unauthorized Space",
            "description": "Should not be created",
        }

        with patch("app.routes_spaces.get_db", return_value=fake_spaces_db):
            response = unauthenticated_client.post("/spaces", json=space_data)

        assert response.status_code in [401, 403]  # Either is acceptable


class TestSpacesGet:
    """Test getting individual family spaces."""

    def test_get_space_success(self, client, fake_spaces_db):
        """Test successful retrieval of existing space."""
        with patch("app.routes_spaces.get_db", return_value=fake_spaces_db):
            response = client.get("/spaces/demo")

        assert response.status_code == 200
        space = response.json()

        assert space["id"] == "demo"
        assert space["name"] == "Demo Family"
        assert space["description"] == "Demo family space"
        assert space["created_by"] == "system"

    def test_get_space_not_found(self, client, fake_spaces_db):
        """Test retrieving non-existent space returns 404."""
        with patch("app.routes_spaces.get_db", return_value=fake_spaces_db):
            response = client.get("/spaces/nonexistent")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"]


class TestSpacesDelete:
    """Test deleting family spaces."""

    def test_delete_space_success(self, authenticated_admin_client, fake_spaces_db):
        """Test successful deletion of existing space by admin."""
        with patch("app.routes_spaces.get_db", return_value=fake_spaces_db):
            response = authenticated_admin_client.delete("/spaces/demo")

        assert response.status_code == 200
        assert "deleted successfully" in response.json()["message"]

    def test_delete_space_not_found(self, authenticated_admin_client, fake_spaces_db):
        """Test deleting non-existent space returns 404."""
        with patch("app.routes_spaces.get_db", return_value=fake_spaces_db):
            response = authenticated_admin_client.delete("/spaces/nonexistent")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"]

    def test_delete_space_unauthorized(self, unauthenticated_client, fake_spaces_db):
        """Test deleting space without admin access fails."""
        with patch("app.routes_spaces.get_db", return_value=fake_spaces_db):
            response = unauthenticated_client.delete("/spaces/demo")

        assert response.status_code in [401, 403]  # Either is acceptable


class TestUserSpaceFunctions:
    """Test user space utility functions."""

    def test_get_user_space_existing_user(self, fake_spaces_db):
        """Test getting space for existing user."""
        with patch("app.routes_spaces.get_db", return_value=fake_spaces_db):
            space = get_user_space("test_user")

        assert space == "demo"

    def test_get_user_space_nonexistent_user(self, fake_spaces_db):
        """Test getting space for non-existent user returns default."""
        with patch("app.routes_spaces.get_db", return_value=fake_spaces_db):
            space = get_user_space("nonexistent_user")

        assert space == "demo"

    def test_get_user_space_user_without_space(self, fake_spaces_db):
        """Test getting space for user without current_space set."""
        # Create user without current_space
        fake_spaces_db.collection("users").document("no_space_user").set(
            {"username": "no_space_user"}
        )

        with patch("app.routes_spaces.get_db", return_value=fake_spaces_db):
            space = get_user_space("no_space_user")

        assert space == "demo"

    def test_set_user_space(self, fake_spaces_db):
        """Test setting user's current space."""
        with patch("app.routes_spaces.get_db", return_value=fake_spaces_db):
            set_user_space("test_user", "smith_family")

        # Verify the space was updated
        user_doc = fake_spaces_db.collection("users").document("test_user").get()
        assert user_doc.to_dict()["current_space"] == "smith_family"


class TestEnsureDefaultSpaces:
    """Test default spaces creation."""

    def test_ensure_default_spaces_creates_missing(self):
        """Test that default spaces are created when missing."""
        empty_db = FakeDB()

        with patch("app.routes_spaces.get_db", return_value=empty_db):
            ensure_default_spaces()

        # Check that default spaces were created
        expected_spaces = ["demo", "karunakaran", "anand", "kullatira"]

        for space_id in expected_spaces:
            doc = empty_db.collection("family_spaces").document(space_id).get()
            assert doc.exists
            data = doc.to_dict()
            assert data["created_by"] == "system"
            assert "created_at" in data

    def test_ensure_default_spaces_preserves_existing(self, fake_spaces_db):
        """Test that existing spaces are not overwritten."""
        original_demo = fake_spaces_db.collection("family_spaces").document("demo").get().to_dict()

        with patch("app.routes_spaces.get_db", return_value=fake_spaces_db):
            ensure_default_spaces()

        # Check that existing demo space was not overwritten
        current_demo = fake_spaces_db.collection("family_spaces").document("demo").get().to_dict()
        assert current_demo == original_demo
        assert current_demo["created_by"] == "system"  # Original value

        # Check that other default spaces were still created
        kullatira_doc = fake_spaces_db.collection("family_spaces").document("kullatira").get()
        assert kullatira_doc.exists
