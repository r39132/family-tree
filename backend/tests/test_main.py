from fastapi.testclient import TestClient

from app.main import app


def test_health_check():
    """Test health check endpoint"""
    client = TestClient(app)
    response = client.get("/healthz")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"


def test_cors_middleware():
    """Test CORS middleware is configured"""
    client = TestClient(app)
    # Test preflight request
    response = client.options(
        "/healthz",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET",
        },
    )
    # Should allow CORS or return 200
    assert response.status_code in [200, 204]


def test_app_title():
    """Test app configuration"""
    assert app.title == "Family Tree API"
