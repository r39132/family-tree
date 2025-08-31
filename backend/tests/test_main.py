from fastapi.testclient import TestClient

from app.main import app


def test_health_check():
    """Test health check endpoint"""
    client = TestClient(app)
    response = client.get("/healthz")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "version" in data


def test_app_title():
    """Test app configuration"""
    assert app.title == "Family Tree API"
