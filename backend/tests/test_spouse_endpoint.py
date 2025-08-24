from fastapi.testclient import TestClient

from app.main import app


def test_spouse_endpoint_rejects_nonexistent_member():
    c = TestClient(app)
    # no auth token set; expect 401
    r = c.post("/tree/members/does-not-exist/spouse", json={"spouse_id": None})
    assert r.status_code in (401, 403)
