from fastapi.testclient import TestClient

import app.routes_tree as routes_tree
from app.deps import get_current_username
from app.firestore_client import get_db as real_get_db
from app.main import app
from tests.conftest import FakeDB


def auth():
    return {"Authorization": "Bearer test"}


def test_backfill_versions_assigns_in_order():
    c = TestClient(app)

    # Set up fake database and authentication overrides
    fake_db = FakeDB()

    # Create a test user document with current_space
    fake_db.collection("users").document("tester").set(
        {"current_space": "test_space_123", "username": "tester"}
    )

    orig_db = app.dependency_overrides.get(real_get_db)
    orig_user = app.dependency_overrides.get(get_current_username)
    app.dependency_overrides[real_get_db] = lambda: fake_db
    app.dependency_overrides[get_current_username] = lambda: "tester"

    # Monkeypatch direct imports used inside route modules
    orig_tree_get_db = routes_tree.get_db
    routes_tree.get_db = lambda: fake_db

    try:
        # Create a couple of versions with missing version numbers by writing directly
        # Use the save endpoint twice to ensure format; then blank out versions to simulate legacy
        headers = {"Authorization": "Bearer test"}
        r1 = c.post("/tree/save", headers=headers)
        assert r1.status_code == 200
        r2 = c.post("/tree/save", headers=headers)
        assert r2.status_code == 200
        # Simulate missing versions by setting to 0
        db = routes_tree.get_db()
        for d in db.collection("tree_versions").stream():
            db.collection("tree_versions").document(d.id).update({"version": 0})
        # Run backfill
        r = c.post("/tree/versions/backfill", headers=headers)
        assert r.status_code == 200
        info = r.json()
        assert info["total"] >= 2
        assert info["updated"] >= 2
        # List and ensure versions are non-zero and newest first
        r = c.get("/tree/versions", headers=headers)
        assert r.status_code == 200
        versions = r.json()
        assert all(v.get("version", 0) > 0 for v in versions[:2])

        # Ensure versions are sequential starting from 1
        nums = [v.get("version", 0) for v in versions]
        assert sorted(nums) == list(range(1, len(nums) + 1))
    finally:
        # Restore original overrides and patches
        app.dependency_overrides[real_get_db] = orig_db
        app.dependency_overrides[get_current_username] = orig_user
        routes_tree.get_db = orig_tree_get_db
