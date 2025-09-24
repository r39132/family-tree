"""Tests for admin functionality."""

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app.deps import get_current_username
from app.main import app
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

    # Also need to mock require_admin dependency since admin endpoints use it directly
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
def fake_admin_db():
    """Set up fake database with admin test data."""
    fake_db = FakeDB()

    # Create test users
    fake_db.collection("users").document("admin_user").set(
        {
            "email": "admin@test.com",
            "roles": ["admin"],
            "first_login_at": 1640995200,  # epoch seconds
            "last_login_at": 1640995200,
            "login_count": 5,
        }
    )

    fake_db.collection("users").document("regular_user").set(
        {
            "email": "user@test.com",
            "roles": [],
            "first_login_at": 1640995300,
            "last_login_at": 1640995400,
            "login_count": 3,
        }
    )

    fake_db.collection("users").document("evicted_user").set(
        {
            "email": "evicted@test.com",
            "roles": [],
            "evicted_at": 1640995500,
            "sessions_invalid_after": "2023-01-01T00:00:00Z",
        }
    )

    return fake_db


class TestListUsers:
    """Test listing users endpoint."""

    def test_list_users_success(self, authenticated_admin_client, fake_admin_db):
        """Test successful listing of users by admin."""
        with patch("app.routes_admin.get_db", return_value=fake_admin_db):
            response = authenticated_admin_client.get("/admin/users")

        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is True
        assert len(data["users"]) == 3

        # Check users are sorted by id
        users = data["users"]
        assert users[0]["id"] == "admin_user"
        assert users[1]["id"] == "evicted_user"
        assert users[2]["id"] == "regular_user"

        # Check admin user structure
        admin_user = users[0]
        assert admin_user["email"] == "admin@test.com"
        assert admin_user["is_admin"] is True
        assert admin_user["login_count"] == 5

        # Check regular user
        regular_user = users[2]
        assert regular_user["is_admin"] is False
        assert regular_user["login_count"] == 3

    def test_list_users_unauthorized(self, unauthenticated_client, fake_admin_db):
        """Test listing users without admin access fails."""
        with patch("app.routes_admin.get_db", return_value=fake_admin_db):
            response = unauthenticated_client.get("/admin/users")
        assert response.status_code in [401, 403]  # Either is acceptable


class TestEvictUser:
    """Test user eviction functionality."""

    def test_evict_user_success(self, authenticated_admin_client, fake_admin_db):
        """Test successful user eviction by admin."""
        with (
            patch("app.routes_admin.get_db", return_value=fake_admin_db),
            patch("app.routes_admin.log_admin_action") as mock_log,
        ):
            response = authenticated_admin_client.post("/admin/users/regular_user/evict")

        assert response.status_code == 200
        assert response.json()["ok"] is True

        # Check user was evicted in database
        user_doc = fake_admin_db.collection("users").document("regular_user").get()
        user_data = user_doc.to_dict()
        assert "sessions_invalid_after" in user_data
        assert "evicted_at" in user_data

        # Check admin action was logged
        mock_log.assert_called_once()

    def test_evict_user_not_found(self, authenticated_admin_client, fake_admin_db):
        """Test evicting non-existent user returns 404."""
        with patch("app.routes_admin.get_db", return_value=fake_admin_db):
            response = authenticated_admin_client.post("/admin/users/nonexistent/evict")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"]

    def test_evict_user_unauthorized(self, unauthenticated_client, fake_admin_db):
        """Test evicting user without admin access fails."""
        with patch("app.routes_admin.get_db", return_value=fake_admin_db):
            response = unauthenticated_client.post("/admin/users/regular_user/evict")
        assert response.status_code in [401, 403]  # Either is acceptable


class TestUnevictUser:
    """Test user uneviction functionality."""

    def test_unevict_user_success(self, authenticated_admin_client, fake_admin_db):
        """Test successful user uneviction by admin."""
        with (
            patch("app.routes_admin.get_db", return_value=fake_admin_db),
            patch("app.routes_admin.log_admin_action") as mock_log,
        ):
            response = authenticated_admin_client.post("/admin/users/evicted_user/unevict")

        assert response.status_code == 200
        assert response.json()["ok"] is True

        # Check user was unevicted in database
        user_doc = fake_admin_db.collection("users").document("evicted_user").get()
        user_data = user_doc.to_dict()
        assert user_data.get("sessions_invalid_after") is None
        assert user_data.get("evicted_at") is None

        # Check admin action was logged
        mock_log.assert_called_once()

    def test_unevict_user_not_found(self, authenticated_admin_client, fake_admin_db):
        """Test unevicting non-existent user returns 404."""
        with patch("app.routes_admin.get_db", return_value=fake_admin_db):
            response = authenticated_admin_client.post("/admin/users/nonexistent/unevict")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"]


class TestPromoteAdmin:
    """Test admin promotion functionality."""

    def test_promote_user_success(self, authenticated_admin_client, fake_admin_db):
        """Test successful user promotion to admin."""
        with (
            patch("app.routes_admin.get_db", return_value=fake_admin_db),
            patch("app.routes_admin.log_admin_action") as mock_log,
        ):
            response = authenticated_admin_client.post("/admin/users/regular_user/promote")

        assert response.status_code == 200
        assert response.json()["ok"] is True

        # Check user was promoted in database
        user_doc = fake_admin_db.collection("users").document("regular_user").get()
        user_data = user_doc.to_dict()
        assert "admin" in user_data["roles"]

        # Check admin action was logged
        mock_log.assert_called_once()

    def test_promote_already_admin(self, authenticated_admin_client, fake_admin_db):
        """Test promoting user who is already admin."""
        with (
            patch("app.routes_admin.get_db", return_value=fake_admin_db),
            patch("app.routes_admin.log_admin_action") as mock_log,
        ):
            response = authenticated_admin_client.post("/admin/users/admin_user/promote")

        assert response.status_code == 200
        assert response.json()["ok"] is True

        # Check roles were not duplicated
        user_doc = fake_admin_db.collection("users").document("admin_user").get()
        user_data = user_doc.to_dict()
        admin_count = user_data["roles"].count("admin")
        assert admin_count == 1

        # Check admin action was logged
        mock_log.assert_called_once()

    def test_promote_user_not_found(self, authenticated_admin_client, fake_admin_db):
        """Test promoting non-existent user returns 404."""
        with patch("app.routes_admin.get_db", return_value=fake_admin_db):
            response = authenticated_admin_client.post("/admin/users/nonexistent/promote")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"]


class TestDemoteAdmin:
    """Test admin demotion functionality."""

    def test_demote_admin_success(self, authenticated_admin_client, fake_admin_db):
        """Test successful admin demotion to regular user."""
        with (
            patch("app.routes_admin.get_db", return_value=fake_admin_db),
            patch("app.routes_admin.log_admin_action") as mock_log,
        ):
            response = authenticated_admin_client.post("/admin/users/admin_user/demote")

        assert response.status_code == 200
        assert response.json()["ok"] is True

        # Check user was demoted in database
        user_doc = fake_admin_db.collection("users").document("admin_user").get()
        user_data = user_doc.to_dict()
        assert "admin" not in user_data["roles"]

        # Check admin action was logged
        mock_log.assert_called_once()

    def test_demote_regular_user(self, authenticated_admin_client, fake_admin_db):
        """Test demoting user who is not admin."""
        with (
            patch("app.routes_admin.get_db", return_value=fake_admin_db),
            patch("app.routes_admin.log_admin_action") as mock_log,
        ):
            response = authenticated_admin_client.post("/admin/users/regular_user/demote")

        assert response.status_code == 200
        assert response.json()["ok"] is True

        # Should not cause errors even if user is not admin
        mock_log.assert_called_once()

    def test_demote_user_not_found(self, authenticated_admin_client, fake_admin_db):
        """Test demoting non-existent user returns 404."""
        with patch("app.routes_admin.get_db", return_value=fake_admin_db):
            response = authenticated_admin_client.post("/admin/users/nonexistent/demote")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"]


class TestAdminEdgeCases:
    """Test edge cases and error conditions."""

    def test_user_with_no_roles_field(self, authenticated_admin_client):
        """Test handling users without roles field."""
        fake_db = FakeDB()
        fake_db.collection("users").document("no_roles_user").set(
            {
                "email": "noroles@test.com"
                # No roles field
            }
        )

        with patch("app.routes_admin.get_db", return_value=fake_db):
            response = authenticated_admin_client.get("/admin/users")

        assert response.status_code == 200
        users = response.json()["users"]
        assert len(users) == 1
        assert users[0]["is_admin"] is False

    def test_user_with_null_roles(self, authenticated_admin_client):
        """Test handling users with null roles."""
        fake_db = FakeDB()
        fake_db.collection("users").document("null_roles_user").set(
            {"email": "nullroles@test.com", "roles": None}
        )

        with (
            patch("app.routes_admin.get_db", return_value=fake_db),
            patch("app.routes_admin.log_admin_action"),
        ):
            # Should handle null roles gracefully
            response = authenticated_admin_client.post("/admin/users/null_roles_user/promote")

        assert response.status_code == 200
