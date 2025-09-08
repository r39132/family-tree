from fastapi.testclient import TestClient

from app.main import app


def test_health():
    c = TestClient(app)
    r = c.get("/status")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"
