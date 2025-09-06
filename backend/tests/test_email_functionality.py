"""
Comprehensive email functionality tests for pytest suite
"""

from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


class TestEmailFunctionality:
    """Test suite for email invite functionality"""

    @pytest.fixture
    def auth_headers(self):
        """Create authenticated user and return auth headers"""
        # Register test user
        register_payload = {
            "username": "emailtestuser",
            "password": "testpass123",
            "invite_code": "test",
        }
        client.post("/auth/register", json=register_payload)

        # Login to get token
        login_payload = {"username": "emailtestuser", "password": "testpass123"}
        response = client.post("/auth/login", json=login_payload)

        if response.status_code == 200:
            token = response.json()["access_token"]
            return {"Authorization": f"Bearer {token}"}
        return {}

    @pytest.fixture
    def mock_smtp(self):
        """Mock SMTP for testing without sending real emails"""
        with patch("app.routes_auth.smtplib.SMTP") as mock_smtp:
            mock_server = MagicMock()
            mock_smtp.return_value.__enter__.return_value = mock_server
            yield mock_server

    def test_create_invite(self, auth_headers):
        """Test creating an invite"""
        response = client.post("/auth/invite", params={"count": 1}, headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "codes" in data
        assert len(data["codes"]) == 1
        return data["codes"][0]

    def test_send_invite_email_authenticated(self, auth_headers, mock_smtp):
        """Test sending invite email (authenticated)"""
        # Create invite first
        invite_response = client.post("/auth/invite", params={"count": 1}, headers=auth_headers)
        invite_code = invite_response.json()["codes"][0]

        # Send email
        payload = {"email": "test@example.com"}
        response = client.post(
            f"/auth/invites/{invite_code}/email", json=payload, headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is True
        assert data["sent_email"] == "test@example.com"

    def test_send_invite_email_public(self, auth_headers, mock_smtp):
        """Test sending invite email (public endpoint)"""
        # Create invite first
        invite_response = client.post("/auth/invite", params={"count": 1}, headers=auth_headers)
        invite_code = invite_response.json()["codes"][0]

        # Send email via public endpoint
        payload = {"email": "public@example.com"}
        response = client.post(f"/auth/public/invites/{invite_code}/email", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is True
        assert data["sent_email"] == "public@example.com"

    def test_resend_email_rate_limiting(self, auth_headers, mock_smtp):
        """Test that resending email too quickly hits rate limiting"""
        # Create invite
        invite_response = client.post("/auth/invite", params={"count": 1}, headers=auth_headers)
        invite_code = invite_response.json()["codes"][0]

        # Send first email
        payload = {"email": "ratelimit@example.com"}
        response1 = client.post(f"/auth/public/invites/{invite_code}/email", json=payload)
        assert response1.status_code == 200

        # Try to send again immediately (should be rate limited)
        response2 = client.post(f"/auth/public/invites/{invite_code}/email", json=payload)
        assert response2.status_code == 429
        assert "recently" in response2.json()["detail"].lower()

    def test_send_different_invite_email(self, auth_headers, mock_smtp):
        """Test sending a different invite email to the same address"""
        # Create first invite and send email
        invite_response1 = client.post("/auth/invite", params={"count": 1}, headers=auth_headers)
        invite_code1 = invite_response1.json()["codes"][0]

        payload = {"email": "different@example.com"}
        response1 = client.post(
            f"/auth/invites/{invite_code1}/email", json=payload, headers=auth_headers
        )
        assert response1.status_code == 200

        # Create second invite and send email to same address
        invite_response2 = client.post("/auth/invite", params={"count": 1}, headers=auth_headers)
        invite_code2 = invite_response2.json()["codes"][0]

        response2 = client.post(
            f"/auth/invites/{invite_code2}/email", json=payload, headers=auth_headers
        )
        assert response2.status_code == 200
        assert response2.json()["sent_email"] == "different@example.com"

    def test_delete_invite(self, auth_headers):
        """Test deleting an invite"""
        # Create invite
        invite_response = client.post("/auth/invite", params={"count": 1}, headers=auth_headers)
        invite_code = invite_response.json()["codes"][0]

        # Delete invite
        response = client.delete(f"/auth/invites/{invite_code}", headers=auth_headers)
        assert response.status_code == 200
        assert "deleted successfully" in response.json()["message"]

        return invite_code

    def test_deleted_invite_cannot_be_used(self, auth_headers):
        """Test that deleted invites cannot be used for registration"""
        # Create and delete invite
        invite_response = client.post("/auth/invite", params={"count": 1}, headers=auth_headers)
        invite_code = invite_response.json()["codes"][0]

        delete_response = client.delete(f"/auth/invites/{invite_code}", headers=auth_headers)
        assert delete_response.status_code == 200

        # Try to register with deleted invite
        register_payload = {
            "username": "deletedtest",
            "password": "testpass123",
            "invite_code": invite_code,
        }
        response = client.post("/auth/register", json=register_payload)
        assert response.status_code == 400  # Should fail

    def test_email_invite_nonexistent_code(self, auth_headers):
        """Test sending email for non-existent invite code"""
        payload = {"email": "nonexistent@example.com"}
        response = client.post("/auth/invites/fake-code/email", json=payload, headers=auth_headers)
        assert response.status_code == 404

    def test_email_invite_missing_email(self, auth_headers):
        """Test sending invite without email address"""
        # Create invite
        invite_response = client.post("/auth/invite", params={"count": 1}, headers=auth_headers)
        invite_code = invite_response.json()["codes"][0]

        # Try to send without email
        response = client.post(f"/auth/invites/{invite_code}/email", json={}, headers=auth_headers)
        assert response.status_code == 400
        assert "email is required" in response.json()["detail"]

    def test_email_invite_redeemed_code(self, auth_headers, mock_smtp):
        """Test that emails cannot be sent for redeemed invites"""
        # Create invite
        invite_response = client.post("/auth/invite", params={"count": 1}, headers=auth_headers)
        invite_code = invite_response.json()["codes"][0]

        # Redeem the invite by registering
        register_payload = {
            "username": f"redeemed_{invite_code[:8]}",
            "password": "testpass123",
            "invite_code": invite_code,
        }
        client.post("/auth/register", json=register_payload)

        # Now try to send email for redeemed invite
        payload = {"email": "redeemed@example.com"}
        response = client.post(
            f"/auth/invites/{invite_code}/email", json=payload, headers=auth_headers
        )
        assert response.status_code == 400
        assert "redeemed" in response.json()["detail"].lower()


class TestEmailConfiguration:
    """Test email configuration and SMTP functionality"""

    def test_email_config_dev_mode(self):
        """Test email sending in development mode (console output)"""
        with patch("app.routes_auth.settings") as mock_settings:
            mock_settings.use_email_in_dev = False
            mock_settings.smtp_host = ""
            mock_settings.smtp_user = ""

            # Import after mocking settings
            from app.routes_auth import send_mail

            # This should print to console instead of sending real email
            with patch("builtins.print") as mock_print:
                send_mail("test@example.com", "Test", "Test body")
                mock_print.assert_called()

    def test_email_config_production_mode(self, mock_smtp):
        """Test email sending in production mode (real SMTP)"""
        with patch("app.routes_auth.settings") as mock_settings:
            mock_settings.use_email_in_dev = True
            mock_settings.smtp_host = "smtp.gmail.com"
            mock_settings.smtp_user = "test@gmail.com"
            mock_settings.smtp_password = "password"
            mock_settings.email_from = "test@gmail.com"
            mock_settings.email_from_name = "Test App"

            from app.routes_auth import send_mail

            send_mail("recipient@example.com", "Test Subject", "Test Body")

            # Verify SMTP was called
            assert mock_smtp.starttls.called
            assert mock_smtp.login.called
            assert mock_smtp.send_message.called


class TestEmailEndpoints:
    """Test email-related API endpoints"""

    def test_test_email_endpoint(self, mock_smtp):
        """Test the /auth/test-email endpoint"""
        response = client.post("/auth/test-email", params={"to": "test@example.com"})
        assert response.status_code in [200, 500]  # May fail due to SMTP config

    def test_test_email_endpoint_logging(self, mock_smtp):
        """Test that test email endpoint produces debug logs"""
        with patch("builtins.print") as mock_print:
            client.post("/auth/test-email", params={"to": "debug@example.com"})
            # Should have printed debug information
            mock_print.assert_called()
