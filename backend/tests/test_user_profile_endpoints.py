from base64 import b64encode

from fastapi.testclient import TestClient

import app.routes_user as routes_user
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
    # Monkeypatch direct imports used inside route module
    module._orig_user_get_db = routes_user.get_db
    routes_user.get_db = lambda: fake_db


def teardown_module(module):
    if module._orig_db is not None:
        app.dependency_overrides[real_get_db] = module._orig_db
    if module._orig_user is not None:
        app.dependency_overrides[get_current_username] = module._orig_user
    routes_user.get_db = module._orig_user_get_db


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


def _auth_headers():
    # With dependency override in place, the header value itself is not validated
    return {"Authorization": "Bearer test"}


def test_get_profile_not_found():
    client = TestClient(app)
    r = client.get("/user/profile", headers=_auth_headers())
    assert r.status_code == 404
    assert r.json()["detail"] == "User not found"


def test_get_profile_success():
    client = TestClient(app)
    # Seed user document
    fake_db.collection("users").document("tester").set(
        {
            "email": "tester@example.com",
            "first_name": "Test",
            "last_name": "User",
            "roles": ["member"],
            "profile_photo_data_url": "data:image/png;base64,{}".format(b64encode(b"png").decode()),
        }
    )

    r = client.get("/user/profile", headers=_auth_headers())
    assert r.status_code == 200
    data = r.json()
    assert data["username"] == "tester"
    assert data["email"] == "tester@example.com"
    assert data["first_name"] == "Test"
    assert data["last_name"] == "User"
    assert data["roles"] == ["member"]
    assert data["profile_photo_data_url"].startswith("data:image/png;base64,")


def test_update_profile_success_partial_then_full():
    client = TestClient(app)
    # Seed user document
    fake_db.collection("users").document("tester").set(
        {"email": "t@e.com", "first_name": "Old", "last_name": "Name"}
    )

    # Partial update (first name only)
    r1 = client.put("/user/profile", json={"first_name": "New"}, headers=_auth_headers())
    assert r1.status_code == 200
    assert r1.json()["first_name"] == "New"
    assert r1.json()["last_name"] == "Name"

    # Full update (last name)
    r2 = client.put("/user/profile", json={"last_name": "Last"}, headers=_auth_headers())
    assert r2.status_code == 200
    assert r2.json()["first_name"] == "New"
    assert r2.json()["last_name"] == "Last"

    # Persisted in DB
    doc = fake_db.collection("users").document("tester").get()
    assert doc.exists
    saved = doc.to_dict()
    assert saved["first_name"] == "New"
    assert saved["last_name"] == "Last"


def test_update_profile_validation_errors():
    client = TestClient(app)
    # Seed user document
    fake_db.collection("users").document("tester").set({"email": "t@e.com"})

    # Empty first name after trim
    r1 = client.put("/user/profile", json={"first_name": "  "}, headers=_auth_headers())
    assert r1.status_code == 422
    # Too long last name
    r2 = client.put(
        "/user/profile",
        json={"last_name": "x" * 51},
        headers=_auth_headers(),
    )
    assert r2.status_code == 422


def test_upload_profile_photo_success():
    client = TestClient(app)
    fake_db.collection("users").document("tester").set({"email": "t@e.com"})
    # Create a tiny "image" payload (validator doesn't check magic bytes, only size & header)
    raw = b"small-bytes"
    data_url = "data:image/png;base64," + b64encode(raw).decode()

    r = client.post(
        "/user/profile/photo",
        json={"image_data_url": data_url},
        headers=_auth_headers(),
    )
    assert r.status_code == 200
    assert r.json()["profile_photo_data_url"] == data_url

    # Persisted
    doc = fake_db.collection("users").document("tester").get()
    assert doc.exists
    assert doc.to_dict()["profile_photo_data_url"] == data_url


def test_upload_profile_photo_invalid_format_and_base64_and_too_large():
    client = TestClient(app)
    fake_db.collection("users").document("tester").set({"email": "t@e.com"})

    # Invalid header
    bad_header = "data:text/plain;base64," + b64encode(b"x").decode()
    r1 = client.post(
        "/user/profile/photo",
        json={"image_data_url": bad_header},
        headers=_auth_headers(),
    )
    assert r1.status_code == 422

    # Invalid base64
    bad_b64 = "data:image/png;base64,not-base64!!"
    r2 = client.post(
        "/user/profile/photo",
        json={"image_data_url": bad_b64},
        headers=_auth_headers(),
    )
    assert r2.status_code == 422

    # Too large (decoded > 256KB)
    too_big_raw = b"a" * (262_144 + 1)
    too_big = "data:image/jpeg;base64," + b64encode(too_big_raw).decode()
    r3 = client.post(
        "/user/profile/photo",
        json={"image_data_url": too_big},
        headers=_auth_headers(),
    )
    assert r3.status_code == 422


def test_update_preferences_sets_last_accessed_space():
    client = TestClient(app)
    fake_db.collection("family_spaces").document("demo").set({"name": "Demo"})
    fake_db.collection("users").document("tester").set({
        "email": "tester@example.com",
        "current_space": "demo",
        "last_accessed_space_id": None,
    })

    r = client.patch(
        "/user/preferences",
        json={"last_accessed_space_id": "demo"},
        headers=_auth_headers(),
    )

    assert r.status_code == 200
    data = r.json()
    assert data["current_space"] == "demo"
    assert data["last_accessed_space_id"] == "demo"

    doc = fake_db.collection("users").document("tester").get()
    assert doc.exists
    saved = doc.to_dict()
    assert saved["current_space"] == "demo"
    assert saved["last_accessed_space_id"] == "demo"


def test_update_preferences_unknown_space_rejected():
    client = TestClient(app)
    fake_db.collection("users").document("tester").set({"email": "tester@example.com"})

    r = client.patch(
        "/user/preferences",
        json={"last_accessed_space_id": "missing"},
        headers=_auth_headers(),
    )

    assert r.status_code == 404
    assert r.json()["detail"] == "Family space not found"
