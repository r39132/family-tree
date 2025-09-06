"""Additional tests for main.py and missed coverage areas."""

from fastapi.testclient import TestClient

from app.main import app


def test_app_startup():
    """Test that the FastAPI app can be created and has basic properties."""
    assert app.title is not None
    assert hasattr(app, "routes")


def test_cors_middleware():
    """Test that CORS middleware is properly configured."""
    client = TestClient(app)

    # Test preflight request
    response = client.options(
        "/",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "Content-Type",
        },
    )

    # Should not return 405 Method Not Allowed for OPTIONS
    assert response.status_code != 405


def test_router_inclusion():
    """Test that routers are properly included in the app."""
    # Check that the app has routes from our routers
    route_paths = [route.path for route in app.routes if hasattr(route, "path")]

    # Should have routes from different routers
    assert any("/auth" in path for path in route_paths)
    assert any("/tree" in path for path in route_paths)
    assert any("/events" in path for path in route_paths)
