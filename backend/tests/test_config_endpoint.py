from fastapi.testclient import TestClient

from app.main import app


def test_config_endpoint_returns_public_settings():
    client = TestClient(app)
    r = client.get("/config")
    assert r.status_code == 200
    data = r.json()
    assert "enable_map" in data
    assert "google_maps_api_key" in data
    assert "require_invite" in data
