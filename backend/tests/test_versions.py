from fastapi.testclient import TestClient

import app.routes_tree as routes_tree
from app.main import app


def auth():
    return {"Authorization": "Bearer test"}


def test_save_and_unsaved_and_recover_flow(monkeypatch):
    c = TestClient(app)

    # Create two members and set one as child of the other
    r1 = c.post(
        "/tree/members",
        headers=auth(),
        json={"first_name": "A", "last_name": "One", "dob": "01/01/2000"},
    )
    assert r1.status_code == 200
    m1 = r1.json()
    r2 = c.post(
        "/tree/members",
        headers=auth(),
        json={"first_name": "B", "last_name": "Two", "dob": "02/02/2002"},
    )
    assert r2.status_code == 200
    m2 = r2.json()

    # Make B a root first, then save version 1
    r = c.post("/tree/move", headers=auth(), json={"child_id": m2["id"], "new_parent_id": None})
    assert r.status_code == 200
    r = c.post("/tree/save", headers=auth())
    assert r.status_code == 200
    v1 = r.json()

    # Move B under A, should mark unsaved
    r = c.post("/tree/move", headers=auth(), json={"child_id": m2["id"], "new_parent_id": m1["id"]})
    assert r.status_code == 200
    r = c.get("/tree/unsaved", headers=auth())
    assert r.status_code == 200
    assert r.json()["unsaved"] is True

    # Save as version 2
    r = c.post("/tree/save", headers=auth())
    assert r.status_code == 200
    v2 = r.json()
    assert v2["id"] != v1["id"]
    assert v2["version"] == v1["version"] + 1

    # List versions (v2 first)
    r = c.get("/tree/versions", headers=auth())
    assert r.status_code == 200
    versions = r.json()
    assert len(versions) >= 2
    assert versions[0]["id"] == v2["id"]
    assert versions[0]["version"] >= versions[1]["version"]


def test_backfill_versions_assigns_in_order():
    c = TestClient(app)
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
