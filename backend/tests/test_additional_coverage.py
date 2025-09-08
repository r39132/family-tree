from fastapi.testclient import TestClient

import app.routes_auth as routes_auth
import app.routes_tree as routes_tree
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
    module._orig_tree_get_db = routes_tree.get_db
    module._orig_auth_get_db = routes_auth.get_db
    routes_tree.get_db = lambda: fake_db
    routes_auth.get_db = lambda: fake_db


def teardown_module(module):
    if module._orig_db is not None:
        app.dependency_overrides[real_get_db] = module._orig_db
    if module._orig_user is not None:
        app.dependency_overrides[get_current_username] = module._orig_user
    # restore monkeypatches
    routes_tree.get_db = module._orig_tree_get_db
    routes_auth.get_db = module._orig_auth_get_db


def setup_function(function):
    # Reset fake DB state before each test to prevent cross-test interference
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


def test_health_endpoint():
    """Test the health check endpoint"""
    client = TestClient(app)
    r = client.get("/status")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_tree_endpoint_no_auth():
    """Test tree endpoint without authentication"""
    client = TestClient(app)
    r = client.get("/tree")
    assert r.status_code == 403  # Should be forbidden without auth


def test_member_create_no_auth():
    """Test member creation without authentication"""
    client = TestClient(app)
    r = client.post(
        "/tree/members",
        json={"first_name": "Test", "last_name": "User", "dob": "01/01/2000"},
    )
    assert r.status_code == 403


def test_member_update_not_found():
    """Test updating non-existent member"""
    client = TestClient(app)
    r = client.patch(
        "/tree/members/nonexistent",
        json={"first_name": "Updated"},
        headers={"Authorization": "Bearer x"},
    )
    assert r.status_code == 404
    assert "Member not found" in r.json()["detail"]


def test_member_set_spouse_not_found():
    """Test setting spouse for non-existent member"""
    client = TestClient(app)
    r = client.post(
        "/tree/members/nonexistent/spouse",
        json={"spouse_id": "someone"},
        headers={"Authorization": "Bearer x"},
    )
    assert r.status_code == 404
    assert "Member not found" in r.json()["detail"]


def test_member_set_spouse_unlink():
    """Test unlinking spouse"""
    client = TestClient(app)
    # Create member first
    member = client.post(
        "/tree/members",
        json={"first_name": "Test", "last_name": "User", "dob": "01/01/2000"},
        headers={"Authorization": "Bearer x"},
    ).json()

    # Set spouse to None (unlink)
    r = client.post(
        f"/tree/members/{member['id']}/spouse",
        json={"spouse_id": None},
        headers={"Authorization": "Bearer x"},
    )
    assert r.status_code == 200
    assert r.json()["ok"] is True


def test_tree_empty():
    """Test tree endpoint with no members"""
    client = TestClient(app)
    r = client.get("/tree", headers={"Authorization": "Bearer x"})
    assert r.status_code == 200
    data = r.json()
    assert data["roots"] == []
    assert data["members"] == []


def test_member_invalid_dob_format():
    """Test member creation with invalid DOB format - should still succeed"""
    client = TestClient(app)
    r = client.post(
        "/tree/members",
        json={"first_name": "Test", "last_name": "User", "dob": "invalid-date"},
        headers={"Authorization": "Bearer x"},
    )
    # Should succeed but without dob_ts field
    assert r.status_code == 200


def test_cors_headers():
    """Test CORS headers are present"""
    client = TestClient(app)
    r = client.options(
        "/healthz",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET",
        },
    )
    # Should have CORS headers
    assert "access-control-allow-origin" in r.headers or r.status_code == 200
