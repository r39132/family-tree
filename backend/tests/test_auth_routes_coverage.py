"""Comprehensive tests for app/routes_auth.py to increase coverage."""

from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

import app.routes_auth as routes_auth
from app.deps import get_current_username
from app.firestore_client import get_db as real_get_db
from app.main import app
from tests.test_tree_endpoints import fake_db


def setup_module(module):
    # Override auth and db for all tests in this module
    module._orig_db = app.dependency_overrides.get(real_get_db)
    module._orig_user = app.dependency_overrides.get(get_current_username)
    app.dependency_overrides[real_get_db] = lambda: fake_db
    app.dependency_overrides[get_current_username] = lambda: "tester"
    # Monkeypatch direct imports used inside route modules
    module._orig_auth_get_db = routes_auth.get_db
    routes_auth.get_db = lambda: fake_db


def teardown_module(module):
    if module._orig_db is not None:
        app.dependency_overrides[real_get_db] = module._orig_db
    if module._orig_user is not None:
        app.dependency_overrides[get_current_username] = module._orig_user
    # restore monkeypatches
    routes_auth.get_db = module._orig_auth_get_db


def setup_function(function):
    # Reset fake DB state before each test
    fake_db._store.clear()
    fake_db._store.update(
        {
            "members": {},
            "relations": {},
            "member_keys": {},
            "invites": {},
            "users": {},
        }
    )


class TestSendMail:
    """Test the send_mail function with different configurations."""

    @patch("app.routes_auth.settings")
    def test_send_mail_dev_mode(self, mock_settings):
        """Test send_mail in development mode (no real email)."""
        mock_settings.use_email_in_dev = False
        mock_settings.smtp_host = None
        mock_settings.smtp_user = None

        # Should not raise exception in dev mode
        routes_auth.send_mail("test@example.com", "Test Subject", "Test Body")

    @patch("app.routes_auth.settings")
    @patch("app.routes_auth.smtplib.SMTP")
    def test_send_mail_production_success(self, mock_smtp, mock_settings):
        """Test successful email sending in production mode."""
        mock_settings.use_email_in_dev = True
        mock_settings.smtp_host = "smtp.gmail.com"
        mock_settings.smtp_user = "test@gmail.com"
        mock_settings.smtp_port = 587
        mock_settings.smtp_password = "password"
        mock_settings.email_from = "test@gmail.com"
        mock_settings.email_from_name = "Test App"

        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server

        routes_auth.send_mail("test@example.com", "Test Subject", "Test Body")

        mock_smtp.assert_called_once_with("smtp.gmail.com", 587)
        mock_server.starttls.assert_called_once()
        mock_server.login.assert_called_once_with("test@gmail.com", "password")
        mock_server.send_message.assert_called_once()

    @patch("app.routes_auth.settings")
    @patch("app.routes_auth.smtplib.SMTP")
    def test_send_mail_production_failure(self, mock_smtp, mock_settings):
        """Test email sending failure in production mode."""
        mock_settings.use_email_in_dev = True
        mock_settings.smtp_host = "smtp.gmail.com"
        mock_settings.smtp_user = "test@gmail.com"
        mock_settings.smtp_port = 587
        mock_settings.smtp_password = "password"
        mock_settings.email_from = "test@gmail.com"
        mock_settings.email_from_name = "Test App"

        mock_smtp.side_effect = Exception("SMTP Error")

        with pytest.raises(Exception, match="SMTP Error"):
            routes_auth.send_mail("test@example.com", "Test Subject", "Test Body")


class TestRegistration:
    """Test the registration endpoint."""

    def test_register_success(self):
        """Test successful user registration."""
        client = TestClient(app)

        # Add a valid invite to the database
        fake_db._store["invites"]["test_invite"] = {
            "active": True,
            "email": "test@example.com",
            "created_by": "admin",
        }

        payload = {
            "username": "newuser",
            "email": "test@example.com",
            "password": "password123",
            "invite_code": "test_invite",
        }

        response = client.post("/auth/register", json=payload)
        assert response.status_code == 200

        data = response.json()
        assert data["ok"] is True
        assert "message" in data
        assert "Registered" in data["message"]

        # Check user was created in database
        assert "newuser" in fake_db._store["users"]
        user_data = fake_db._store["users"]["newuser"]
        assert user_data["email"] == "test@example.com"
        assert "password_hash" in user_data

    def test_register_username_exists(self):
        """Test registration with existing username."""
        client = TestClient(app)

        # Add existing user
        fake_db._store["users"]["existinguser"] = {
            "email": "existing@example.com",
            "password_hash": "hash",
        }

        payload = {
            "username": "existinguser",
            "email": "new@example.com",
            "password": "password123",
            "invite_code": "any_code",
        }

        response = client.post("/auth/register", json=payload)
        assert response.status_code == 400
        assert "Username already exists" in response.json()["detail"]

    def test_register_email_already_used(self):
        """Test registration with email already in use."""
        client = TestClient(app)

        # Add existing user with same email
        fake_db._store["users"]["existinguser"] = {
            "email": "test@example.com",
            "password_hash": "hash",
        }

        # Add a valid invite for this test
        fake_db._store["invites"]["test_invite"] = {
            "active": True,
            "email": "test@example.com",
            "created_by": "admin",
        }

        payload = {
            "username": "emailuser",
            "email": "test@example.com",
            "password": "password123",
            "invite_code": "test_invite",
        }

        response = client.post("/auth/register", json=payload)
        assert response.status_code == 400
        assert "already registered" in response.json()["detail"]

    def test_register_invalid_invite(self):
        """Test registration with invalid invite code."""
        client = TestClient(app)

        payload = {
            "username": "inviteuser",
            "email": "invite@example.com",
            "password": "password123",
            "invite_code": "invalid_invite",
        }

        response = client.post("/auth/register", json=payload)
        assert response.status_code == 400
        assert "Invalid invite" in response.json()["detail"]


class TestLogin:
    """Test the login endpoint."""

    def test_login_success(self):
        """Test successful login."""
        client = TestClient(app)

        # Add user with hashed password
        from app.auth_utils import hash_password

        fake_db._store["users"]["testuser"] = {
            "email": "test@example.com",
            "password_hash": hash_password("password123"),
        }

        payload = {"username": "testuser", "password": "password123"}

        response = client.post("/auth/login", json=payload)
        assert response.status_code == 200

        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_login_user_not_found(self):
        """Test login with non-existent user."""
        client = TestClient(app)

        payload = {"username": "nonexistent", "password": "password123"}

        response = client.post("/auth/login", json=payload)
        assert response.status_code == 401
        assert "Invalid credentials" in response.json()["detail"]

    def test_login_wrong_password(self):
        """Test login with wrong password."""
        client = TestClient(app)

        # Add user with hashed password
        from app.auth_utils import hash_password

        fake_db._store["users"]["testuser"] = {
            "email": "test@example.com",
            "password_hash": hash_password("correct_password"),
        }

        payload = {"username": "testuser", "password": "wrong_password"}

        response = client.post("/auth/login", json=payload)
        assert response.status_code == 401
        assert "Invalid credentials" in response.json()["detail"]


class TestForgotPassword:
    """Test the forgot password endpoint."""

    @patch("app.routes_auth.send_mail")
    def test_forgot_password_success(self, mock_send_mail):
        """Test successful forgot password request."""
        client = TestClient(app)

        # Add user
        fake_db._store["users"]["testuser"] = {"email": "test@example.com", "password_hash": "hash"}

        payload = {"username": "testuser", "email": "test@example.com"}

        response = client.post("/auth/forgot", json=payload)
        assert response.status_code == 200
        assert response.json()["ok"] is True

        # Check that email was sent
        mock_send_mail.assert_called_once()
        args = mock_send_mail.call_args[0]
        assert args[0] == "test@example.com"  # to_email
        assert "Password Reset" in args[1]  # subject
        assert "Reset your password" in args[2]  # body

    @patch("app.routes_auth.send_mail")
    def test_forgot_password_email_not_found(self, mock_send_mail):
        """Test forgot password with non-existent email."""
        client = TestClient(app)

        payload = {"username": "nonexistent", "email": "nonexistent@example.com"}

        response = client.post("/auth/forgot", json=payload)
        assert response.status_code == 200
        assert response.json()["ok"] is True

        # Email should not be sent for non-existent users
        mock_send_mail.assert_not_called()


class TestResetPassword:
    """Test the reset password endpoint."""

    def test_reset_password_success(self):
        """Test successful password reset."""
        client = TestClient(app)

        # Add user
        fake_db._store["users"]["testuser"] = {
            "email": "test@example.com",
            "password_hash": "old_hash",
        }

        # Create a valid reset token
        from app.auth_utils import create_reset_token

        reset_token = create_reset_token("testuser")

        payload = {
            "username": "testuser",
            "token": reset_token,
            "new_password": "new_password123",
            "confirm_password": "new_password123",
        }

        response = client.post("/auth/reset", json=payload)
        assert response.status_code == 200
        assert response.json()["ok"] is True

        # Check that password was updated
        user_data = fake_db._store["users"]["testuser"]
        assert user_data["password_hash"] != "old_hash"

    def test_reset_password_invalid_token(self):
        """Test password reset with invalid token."""
        client = TestClient(app)

        payload = {
            "username": "testuser",
            "token": "invalid_token",
            "new_password": "new_password123",
            "confirm_password": "new_password123",
        }

        response = client.post("/auth/reset", json=payload)
        assert response.status_code == 400
        assert "Invalid or expired token" in response.json()["detail"]

    def test_reset_password_user_not_found(self):
        """Test password reset for non-existent user."""
        client = TestClient(app)

        # Create token for non-existent user
        from app.auth_utils import create_reset_token

        reset_token = create_reset_token("nonexistent_user")

        payload = {
            "username": "nonexistent_user",
            "token": reset_token,
            "new_password": "new_password123",
            "confirm_password": "new_password123",
        }

        response = client.post("/auth/reset", json=payload)
        assert response.status_code == 400
        assert "User not found" in response.json()["detail"]
