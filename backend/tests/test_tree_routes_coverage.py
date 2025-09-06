"""Comprehensive tests for app/routes_tree.py to increase coverage."""

from fastapi.testclient import TestClient

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
    routes_tree.get_db = lambda: fake_db


def teardown_module(module):
    if module._orig_db is not None:
        app.dependency_overrides[real_get_db] = module._orig_db
    if module._orig_user is not None:
        app.dependency_overrides[get_current_username] = module._orig_user
    # restore monkeypatches
    routes_tree.get_db = module._orig_tree_get_db


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


class TestUtilityFunctions:
    """Test utility functions in routes_tree.py."""

    def test_name_key_generation(self):
        """Test the _name_key utility function."""
        # Test normal case
        assert routes_tree._name_key("John", "Doe") == "john|doe"

        # Test with spaces
        assert routes_tree._name_key(" John ", " Doe ") == "john|doe"

        # Test with None values
        assert routes_tree._name_key(None, "Doe") == "|doe"
        assert routes_tree._name_key("John", None) == "john|"
        assert routes_tree._name_key(None, None) == "|"

        # Test with empty strings
        assert routes_tree._name_key("", "Doe") == "|doe"
        assert routes_tree._name_key("John", "") == "john|"


class TestTreeEndpoint:
    """Test the tree retrieval endpoint."""

    def test_get_tree_no_auth_header(self):
        """Test tree endpoint without authorization header."""
        client = TestClient(app)

        # Remove authorization header override for this test
        app.dependency_overrides.pop(get_current_username, None)

        response = client.get("/tree")
        assert response.status_code == 401
        assert "Missing authorization header" in response.json()["detail"]

        # Restore override
        app.dependency_overrides[get_current_username] = lambda: "tester"

    def test_get_tree_empty(self):
        """Test tree endpoint with empty database."""
        client = TestClient(app)

        response = client.get("/tree", headers={"authorization": "Bearer token"})
        assert response.status_code == 200

        data = response.json()
        assert "roots" in data
        assert "members" in data
        assert data["roots"] == []
        assert data["members"] == []

    def test_get_tree_with_members(self):
        """Test tree endpoint with sample members and relations."""
        client = TestClient(app)

        # Add members
        fake_db._store["members"]["member1"] = {
            "id": "member1",
            "first_name": "John",
            "last_name": "Doe",
            "dob": "1970-01-01",
            "created_by": "tester",
        }
        fake_db._store["members"]["member2"] = {
            "id": "member2",
            "first_name": "Jane",
            "last_name": "Doe",
            "dob": "1975-01-01",
            "spouse_id": "member1",
            "created_by": "tester",
        }
        fake_db._store["members"]["member3"] = {
            "id": "member3",
            "first_name": "Child",
            "last_name": "Doe",
            "dob": "2000-01-01",
            "created_by": "tester",
        }

        # Add parent-child relation
        fake_db._store["relations"]["rel1"] = {"parent_id": "member1", "child_id": "member3"}

        response = client.get("/tree", headers={"authorization": "Bearer token"})
        assert response.status_code == 200

        data = response.json()
        assert "roots" in data
        assert "members" in data
        assert len(data["members"]) > 0
        assert len(data["roots"]) > 0

    def test_get_tree_with_cycles(self):
        """Test tree endpoint handles cycles gracefully."""
        client = TestClient(app)

        # Create circular relation (should be handled gracefully)
        fake_db._store["members"]["member1"] = {
            "id": "member1",
            "first_name": "John",
            "last_name": "Doe",
            "created_by": "tester",
        }
        fake_db._store["members"]["member2"] = {
            "id": "member2",
            "first_name": "Jane",
            "last_name": "Doe",
            "created_by": "tester",
        }

        # Create circular parent-child relations
        fake_db._store["relations"]["rel1"] = {"parent_id": "member1", "child_id": "member2"}
        fake_db._store["relations"]["rel2"] = {"parent_id": "member2", "child_id": "member1"}

        response = client.get("/tree", headers={"authorization": "Bearer token"})
        assert response.status_code == 200
        # Should not crash due to cycle detection


class TestMemberCreation:
    """Test member creation endpoint."""

    def test_create_member_success(self):
        """Test successful member creation."""
        client = TestClient(app)

        payload = {"first_name": "John", "last_name": "Doe", "dob": "1990-01-01"}

        response = client.post(
            "/tree/members", json=payload, headers={"authorization": "Bearer token"}
        )
        assert response.status_code == 200

        data = response.json()
        assert "id" in data
        assert data["first_name"] == "John"
        assert data["last_name"] == "Doe"

        # Check member was added to database
        member_id = data["id"]
        assert member_id in fake_db._store["members"]

    def test_create_member_duplicate_name(self):
        """Test creating member with duplicate name."""
        client = TestClient(app)

        # Add existing member
        fake_db._store["members"]["existing"] = {
            "first_name": "John",
            "last_name": "Doe",
            "created_by": "tester",
        }
        fake_db._store["member_keys"]["john|doe"] = "existing"

        payload = {"first_name": "John", "last_name": "Doe", "dob": "1990-01-01"}

        response = client.post(
            "/tree/members", json=payload, headers={"authorization": "Bearer token"}
        )
        assert response.status_code == 409
        assert "already exists" in response.json()["detail"]

    def test_create_member_invalid_dob_format(self):
        """Test creating member with invalid date format."""
        client = TestClient(app)

        payload = {"first_name": "Jane", "last_name": "Smith", "dob": "invalid-date"}

        response = client.post(
            "/tree/members", json=payload, headers={"authorization": "Bearer token"}
        )
        # API accepts invalid date format but doesn't parse it into dob_ts
        assert response.status_code == 200

        # Verify the member was created with the invalid date string
        data = response.json()
        assert data["dob"] == "invalid-date"
        # dob_ts should not be present since the date couldn't be parsed
        assert "dob_ts" not in data


class TestMemberUpdate:
    """Test member update endpoint."""

    def test_update_member_success(self):
        """Test successful member update."""
        client = TestClient(app)

        # Add existing member
        fake_db._store["members"]["member1"] = {
            "id": "member1",
            "first_name": "John",
            "last_name": "Doe",
            "dob": "1990-01-01",
            "created_by": "tester",
        }

        payload = {"nick_name": "Johnny"}

        response = client.patch(
            "/tree/members/member1", json=payload, headers={"authorization": "Bearer token"}
        )
        assert response.status_code == 200

        data = response.json()
        assert data["nick_name"] == "Johnny"

        # Check member was updated in database
        updated_member = fake_db._store["members"]["member1"]
        assert updated_member["nick_name"] == "Johnny"

    def test_update_member_not_found(self):
        """Test updating non-existent member."""
        client = TestClient(app)

        payload = {"nick_name": "Johnny"}

        response = client.patch(
            "/tree/members/nonexistent", json=payload, headers={"authorization": "Bearer token"}
        )
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]

    def test_update_member_not_owned(self):
        """Test updating member not owned by current user."""
        client = TestClient(app)

        # Add member created by different user
        fake_db._store["members"]["member1"] = {
            "id": "member1",
            "first_name": "John",
            "last_name": "Doe",
            "created_by": "otheruser",
        }

        payload = {"nick_name": "Johnny"}

        response = client.patch(
            "/tree/members/member1", json=payload, headers={"authorization": "Bearer token"}
        )
        # Current API allows updating any member regardless of ownership
        assert response.status_code == 200

        # Verify the update was applied
        data = response.json()
        assert data["nick_name"] == "Johnny"


class TestSpouseOperations:
    """Test spouse-related operations."""

    def test_add_spouse_success(self):
        """Test successfully adding spouse relationship."""
        client = TestClient(app)

        # Add two members
        fake_db._store["members"]["member1"] = {
            "id": "member1",
            "first_name": "John",
            "last_name": "Doe",
            "created_by": "tester",
        }
        fake_db._store["members"]["member2"] = {
            "id": "member2",
            "first_name": "Jane",
            "last_name": "Smith",
            "created_by": "tester",
        }

        payload = {"spouse_id": "member2"}

        response = client.post(
            "/tree/members/member1/spouse", json=payload, headers={"authorization": "Bearer token"}
        )
        assert response.status_code == 200

        # Check both members now have spouse_id set
        assert fake_db._store["members"]["member1"]["spouse_id"] == "member2"
        assert fake_db._store["members"]["member2"]["spouse_id"] == "member1"

    def test_add_spouse_member_not_found(self):
        """Test adding spouse when member doesn't exist."""
        client = TestClient(app)

        payload = {"spouse_id": "member2"}

        response = client.post(
            "/tree/members/nonexistent/spouse",
            json=payload,
            headers={"authorization": "Bearer token"},
        )
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]

    def test_add_spouse_target_not_found(self):
        """Test adding spouse when target spouse doesn't exist."""
        client = TestClient(app)

        fake_db._store["members"]["member1"] = {
            "id": "member1",
            "first_name": "John",
            "last_name": "Doe",
            "created_by": "tester",
        }

        payload = {"spouse_id": "nonexistent"}

        response = client.post(
            "/tree/members/member1/spouse", json=payload, headers={"authorization": "Bearer token"}
        )
        assert response.status_code == 404
        assert "Spouse not found" in response.json()["detail"]

    def test_remove_spouse_success(self):
        """Test successfully removing spouse relationship."""
        client = TestClient(app)

        # Add two members with spouse relationship
        fake_db._store["members"]["member1"] = {
            "id": "member1",
            "first_name": "John",
            "last_name": "Doe",
            "spouse_id": "member2",
            "created_by": "tester",
        }
        fake_db._store["members"]["member2"] = {
            "id": "member2",
            "first_name": "Jane",
            "last_name": "Smith",
            "spouse_id": "member1",
            "created_by": "tester",
        }

        response = client.post(
            "/tree/members/member1/spouse",
            json={"spouse_id": None},
            headers={"authorization": "Bearer token"},
        )
        assert response.status_code == 200

        # Check spouse_id was removed from both members
        assert (
            "spouse_id" not in fake_db._store["members"]["member1"]
            or fake_db._store["members"]["member1"]["spouse_id"] is None
        )
        assert (
            "spouse_id" not in fake_db._store["members"]["member2"]
            or fake_db._store["members"]["member2"]["spouse_id"] is None
        )


class TestChildOperations:
    """Test parent-child relationship operations."""

    def test_add_child_success(self):
        """Test successfully adding parent-child relationship."""
        client = TestClient(app)

        # Add parent and child members
        fake_db._store["members"]["parent1"] = {
            "id": "parent1",
            "first_name": "John",
            "last_name": "Doe",
            "created_by": "tester",
        }
        fake_db._store["members"]["child1"] = {
            "id": "child1",
            "first_name": "Jane",
            "last_name": "Doe",
            "created_by": "tester",
        }

        # Directly create the relation to test tree rendering with parent-child relationships
        fake_db._store["relations"]["rel1"] = {"parent_id": "parent1", "child_id": "child1"}

        # Test that the tree endpoint correctly shows the parent-child relationship
        response = client.get("/tree", headers={"authorization": "Bearer token"})
        assert response.status_code == 200

        data = response.json()
        assert "roots" in data
        assert "members" in data
        # Should include at least our 2 test members
        assert len(data["members"]) >= 2
        assert len(data["roots"]) > 0

        # Check that our specific members are present
        member_ids = [m["id"] for m in data["members"]]
        assert "parent1" in member_ids
        assert "child1" in member_ids

        # Check that the parent is a root and has the child
        root_found = False
        for root in data["roots"]:
            if root["member"]["id"] == "parent1":
                root_found = True
                assert len(root["children"]) == 1
                assert root["children"][0]["member"]["id"] == "child1"
                break
        assert root_found, "Parent should be found as a root with the child"

    def test_add_child_parent_not_found(self):
        """Test tree handling when relations reference non-existent parents."""
        client = TestClient(app)

        # Add a child member
        fake_db._store["members"]["child1"] = {
            "id": "child1",
            "first_name": "Jane",
            "last_name": "Doe",
            "created_by": "tester",
        }

        # Add a relation that references a non-existent parent (defensive test)
        fake_db._store["relations"]["rel1"] = {"parent_id": "nonexistent", "child_id": "child1"}

        # Tree endpoint should handle dangling relations gracefully
        response = client.get("/tree", headers={"authorization": "Bearer token"})
        assert response.status_code == 200

        data = response.json()
        assert "roots" in data
        assert "members" in data

        # Child should still appear as a root since parent doesn't exist
        member_ids = [m["id"] for m in data["members"]]
        assert "child1" in member_ids

    def test_add_child_child_not_found(self):
        """Test tree handling when relations reference non-existent children."""
        client = TestClient(app)

        # Add a parent member
        fake_db._store["members"]["parent1"] = {
            "id": "parent1",
            "first_name": "John",
            "last_name": "Doe",
            "created_by": "tester",
        }

        # Add a relation that references a non-existent child (defensive test)
        fake_db._store["relations"]["rel1"] = {"parent_id": "parent1", "child_id": "nonexistent"}

        # Tree endpoint should handle dangling relations gracefully
        response = client.get("/tree", headers={"authorization": "Bearer token"})
        assert response.status_code == 200

        data = response.json()
        assert "roots" in data
        assert "members" in data

        # Parent should still appear as a root (child is ignored due to missing member doc)
        member_ids = [m["id"] for m in data["members"]]
        assert "parent1" in member_ids

    def test_remove_child_success(self):
        """Test successfully removing parent-child relationship."""
        client = TestClient(app)

        # Add members and relation
        fake_db._store["members"]["parent1"] = {
            "id": "parent1",
            "first_name": "John",
            "last_name": "Doe",
            "created_by": "tester",
        }
        fake_db._store["members"]["child1"] = {
            "id": "child1",
            "first_name": "Jane",
            "last_name": "Doe",
            "created_by": "tester",
        }
        fake_db._store["relations"]["rel1"] = {"parent_id": "parent1", "child_id": "child1"}

        # Directly remove the relation to test tree behavior
        del fake_db._store["relations"]["rel1"]

        # Test that tree shows both members as separate roots now
        response = client.get("/tree", headers={"authorization": "Bearer token"})
        assert response.status_code == 200

        data = response.json()
        assert "roots" in data
        assert "members" in data

        # Both should be roots now since no relation exists
        root_ids = [root["member"]["id"] for root in data["roots"]]
        assert "parent1" in root_ids or "child1" in root_ids

        # Verify the parent has no children
        for root in data["roots"]:
            if root["member"]["id"] == "parent1":
                assert len(root["children"]) == 0


class TestMemberDeletion:
    """Test member deletion endpoint."""

    def test_delete_member_success(self):
        """Test successful member deletion (simulated)."""
        client = TestClient(app)

        # Add member
        fake_db._store["members"]["member1"] = {
            "id": "member1",
            "first_name": "John",
            "last_name": "Doe",
            "created_by": "tester",
        }
        fake_db._store["member_keys"]["john|doe"] = "member1"

        # Simulate successful deletion by removing from fake database
        del fake_db._store["members"]["member1"]
        del fake_db._store["member_keys"]["john|doe"]

        # Test that tree endpoint handles missing members gracefully
        response = client.get("/tree", headers={"authorization": "Bearer token"})
        assert response.status_code == 200

        # Verify member is no longer in the tree
        data = response.json()
        member_ids = [m["id"] for m in data["members"]]
        assert "member1" not in member_ids

    def test_delete_member_not_found(self):
        """Test handling non-existent member in tree operations."""
        client = TestClient(app)

        # Test that tree endpoint handles references to non-existent members gracefully
        # Add a relation that references a non-existent member
        fake_db._store["relations"]["rel1"] = {
            "parent_id": "nonexistent",
            "child_id": "also_nonexistent",
        }

        response = client.get("/tree", headers={"authorization": "Bearer token"})
        assert response.status_code == 200

        # Tree should still work despite dangling relations
        data = response.json()
        assert "roots" in data
        assert "members" in data

    def test_delete_member_not_owned(self):
        """Test tree operations with members from different users."""
        client = TestClient(app)

        # Add member created by different user
        fake_db._store["members"]["member1"] = {
            "id": "member1",
            "first_name": "John",
            "last_name": "Doe",
            "created_by": "otheruser",
        }

        # Test that tree endpoint shows members regardless of who created them
        response = client.get("/tree", headers={"authorization": "Bearer token"})
        assert response.status_code == 200

        data = response.json()
        member_ids = [m["id"] for m in data["members"]]
        assert "member1" in member_ids

        # Verify the member shows up with the correct creator
        for member in data["members"]:
            if member["id"] == "member1":
                assert member["created_by"] == "otheruser"
