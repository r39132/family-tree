"""
Comprehensive test suite for space-specific functionality in the family tree system.
Tests all endpoints with multi-space scenarios to ensure proper data isolation.
"""

import uuid
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient


# Mock the dependencies before importing the app
@pytest.fixture(autouse=True)
def mock_dependencies():
    with (
        patch("app.deps.get_current_username") as mock_get_username,
        patch("app.firestore_client.get_db") as mock_get_db,
    ):
        yield mock_get_username, mock_get_db


@pytest.fixture
def mock_db():
    """Mock Firestore database with collections"""
    db = MagicMock()

    # Create mock collections
    collections = {
        "users": MagicMock(),
        "family_spaces": MagicMock(),
        "members": MagicMock(),
        "relations": MagicMock(),
        "tree_versions": MagicMock(),
        "tree_state": MagicMock(),
    }

    def collection(name):
        return collections[name]

    db.collection = collection
    return db, collections


@pytest.fixture
def client():
    from app.main import app

    return TestClient(app)


@pytest.fixture
def test_data():
    """Test data for multiple spaces"""
    return {
        "space_a": {
            "id": "space_a_123",
            "name": "Smith Family",
            "users": ["alice_smith", "bob_smith"],
            "members": [
                {
                    "id": "alice_member",
                    "first_name": "Alice",
                    "last_name": "Smith",
                    "space_id": "space_a_123",
                },
                {
                    "id": "bob_member",
                    "first_name": "Bob",
                    "last_name": "Smith",
                    "space_id": "space_a_123",
                },
                {
                    "id": "charlie_member",
                    "first_name": "Charlie",
                    "last_name": "Smith",
                    "space_id": "space_a_123",
                },
            ],
            "relations": [
                {
                    "parent_id": "alice_member",
                    "child_id": "charlie_member",
                    "space_id": "space_a_123",
                },
                {
                    "parent_id": "bob_member",
                    "child_id": "charlie_member",
                    "space_id": "space_a_123",
                },
            ],
        },
        "space_b": {
            "id": "space_b_456",
            "name": "Johnson Family",
            "users": ["david_johnson", "emma_johnson"],
            "members": [
                {
                    "id": "david_member",
                    "first_name": "David",
                    "last_name": "Johnson",
                    "space_id": "space_b_456",
                },
                {
                    "id": "emma_member",
                    "first_name": "Emma",
                    "last_name": "Johnson",
                    "space_id": "space_b_456",
                },
                {
                    "id": "frank_member",
                    "first_name": "Frank",
                    "last_name": "Johnson",
                    "space_id": "space_b_456",
                },
            ],
            "relations": [
                {
                    "parent_id": "david_member",
                    "child_id": "frank_member",
                    "space_id": "space_b_456",
                },
                {"parent_id": "emma_member", "child_id": "frank_member", "space_id": "space_b_456"},
            ],
        },
    }


class TestSpaceIsolation:
    """Test that users can only access their own space data"""

    def setup_mock_user_space(self, mock_collections, username, space_id):
        """Helper to set up user-space mapping"""
        user_doc = MagicMock()
        user_doc.exists = True
        user_doc.to_dict.return_value = {"current_space": space_id, "email": f"{username}@test.com"}
        mock_collections["users"].document.return_value.get.return_value = user_doc

    def setup_mock_space_data(self, mock_collections, space_data):
        """Helper to set up space data in mocks"""
        # Mock members query
        member_docs = []
        for member in space_data["members"]:
            doc = MagicMock()
            doc.to_dict.return_value = member
            doc.id = member["id"]
            member_docs.append(doc)

        mock_collections["members"].where.return_value.stream.return_value = member_docs

        # Mock relations query
        relation_docs = []
        for relation in space_data["relations"]:
            doc = MagicMock()
            doc.to_dict.return_value = relation
            doc.id = f"relation_{uuid.uuid4().hex[:8]}"
            relation_docs.append(doc)

        mock_collections["relations"].where.return_value.stream.return_value = relation_docs

    @patch("app.routes_tree.get_current_username")
    def test_tree_endpoint_space_isolation(self, mock_username, client, mock_db, test_data):
        """Test GET /tree returns only user's space data"""
        db, mock_collections = mock_db

        # Setup Alice in space A
        mock_username.return_value = "alice_smith"
        self.setup_mock_user_space(mock_collections, "alice_smith", "space_a_123")
        self.setup_mock_space_data(mock_collections, test_data["space_a"])

        with patch("app.routes_tree.get_db", return_value=db):
            response = client.get("/tree", headers={"Authorization": "Bearer token"})

        print(f"Response status: {response.status_code}")
        print(f"Response content: {response.text}")
        assert response.status_code == 200
        data = response.json()

        # Should only see space A data
        member_names = [m["first_name"] for m in data.get("members", [])]
        assert "Alice" in member_names
        assert "Bob" in member_names
        assert "Charlie" in member_names

        # Should NOT see space B data
        assert "David" not in member_names
        assert "Emma" not in member_names
        assert "Frank" not in member_names

        # Verify space-specific query was made
        mock_collections["members"].where.assert_called_with("space_id", "==", "space_a_123")


class TestSpaceSpecificActiveVersions:
    """Test space-specific active version management"""

    def setup_mock_user_space(self, mock_collections, username, space_id):
        """Helper to set up user-space mapping"""
        user_doc = MagicMock()
        user_doc.exists = True
        user_doc.to_dict.return_value = {"current_space": space_id, "email": f"{username}@test.com"}
        mock_collections["users"].document.return_value.get.return_value = user_doc

    @patch("app.routes_tree.get_current_username")
    def test_save_creates_space_specific_active_version(
        self, mock_username, client, mock_db, test_data
    ):
        """Test POST /save creates space-specific active version"""
        db, mock_collections = mock_db

        mock_username.return_value = "alice_smith"
        self.setup_mock_user_space(mock_collections, "alice_smith", "space_a_123")

        # Mock relations for snapshot
        relation_docs = []
        for relation in test_data["space_a"]["relations"]:
            doc = MagicMock()
            doc.to_dict.return_value = relation
            relation_docs.append(doc)
        mock_collections["relations"].where.return_value.stream.return_value = relation_docs

        # Mock version document creation
        version_doc = MagicMock()
        version_doc.id = "new_version_123"
        mock_collections["tree_versions"].document.return_value = version_doc

        # Mock existing versions for version numbering
        mock_collections["tree_versions"].where.return_value.stream.return_value = []

        with (
            patch("app.routes_tree.get_db", return_value=db),
            patch("app.routes_tree.utc_now") as mock_now,
            patch("app.routes_tree.to_iso_string") as mock_iso,
        ):
            mock_now.return_value = datetime(2025, 1, 1, 12, 0, 0)
            mock_iso.return_value = "2025-01-01T12:00:00Z"

            response = client.post("/tree/save", headers={"Authorization": "Bearer token"})

        assert response.status_code == 200

        # Verify space-specific active version was set
        mock_collections["tree_state"].document.assert_called_with("active_version_space_a_123")
        active_version_doc = mock_collections["tree_state"].document.return_value
        active_version_doc.set.assert_called_once()

        # Check the active version data includes space_id
        set_call_args = active_version_doc.set.call_args[0][0]
        assert set_call_args["version_id"] == "new_version_123"
        assert set_call_args["space_id"] == "space_a_123"
        assert "updated_at" in set_call_args


class TestCrossSpaceSecurityValidation:
    """Test security validation prevents cross-space access"""

    def setup_mock_user_space(self, mock_collections, username, space_id):
        """Helper to set up user-space mapping"""
        user_doc = MagicMock()
        user_doc.exists = True
        user_doc.to_dict.return_value = {"current_space": space_id}
        mock_collections["users"].document.return_value.get.return_value = user_doc

    @patch("app.routes_tree.get_current_username")
    def test_recover_validates_version_space_ownership(
        self, mock_username, client, mock_db, test_data
    ):
        """Test POST /recover validates user can only recover their space's versions"""
        db, mock_collections = mock_db

        # User A tries to recover a version
        mock_username.return_value = "alice_smith"
        self.setup_mock_user_space(mock_collections, "alice_smith", "space_a_123")

        # Mock a version that belongs to space B (should be rejected)
        version_doc = MagicMock()
        version_doc.exists = True
        version_doc.to_dict.return_value = {
            "space_id": "space_b_456",  # Different space!
            "relations": test_data["space_b"]["relations"],
            "version": 1,
        }
        mock_collections["tree_versions"].document.return_value.get.return_value = version_doc

        with patch("app.routes_tree.get_db", return_value=db):
            response = client.post(
                "/tree/recover",
                json={"version_id": "version_from_space_b"},
                headers={"Authorization": "Bearer token"},
            )

        # Should reject the cross-space recovery attempt
        assert response.status_code == 403
        assert "different space" in response.json()["detail"].lower()


class TestSpaceVersionComparison:
    """Test normalized version comparison logic"""

    def setup_mock_user_space(self, mock_collections, username, space_id):
        """Helper to set up user-space mapping"""
        user_doc = MagicMock()
        user_doc.exists = True
        user_doc.to_dict.return_value = {"current_space": space_id}
        mock_collections["users"].document.return_value.get.return_value = user_doc

    @patch("app.routes_tree.get_current_username")
    def test_relation_comparison_normalization(self, mock_username, client, mock_db, test_data):
        """Test that relation comparison handles ordering and field differences"""
        db, mock_collections = mock_db

        mock_username.return_value = "alice_smith"
        self.setup_mock_user_space(mock_collections, "alice_smith", "space_a_123")

        # Current relations (different order, extra fields)
        current_relations = [
            {"child_id": "child_b", "parent_id": "parent_2", "extra_field": "ignore"},
            {"child_id": "child_a", "parent_id": "parent_1", "space_id": "space_a_123"},
        ]

        # Saved relations (different order, missing space_id)
        saved_relations = [
            {"parent_id": "parent_1", "child_id": "child_a"},
            {"parent_id": "parent_2", "child_id": "child_b"},
        ]

        # Mock current relations
        relation_docs = []
        for relation in current_relations:
            doc = MagicMock()
            doc.to_dict.return_value = relation
            relation_docs.append(doc)
        mock_collections["relations"].where.return_value.stream.return_value = relation_docs

        # Mock active version
        active_version_doc = MagicMock()
        active_version_doc.exists = True
        active_version_doc.to_dict.return_value = {"version_id": "version_123"}
        mock_collections["tree_state"].document.return_value.get.return_value = active_version_doc

        # Mock version document
        version_doc = MagicMock()
        version_doc.exists = True
        version_doc.to_dict.return_value = {"space_id": "space_a_123", "relations": saved_relations}
        mock_collections["tree_versions"].document.return_value.get.return_value = version_doc

        with patch("app.routes_tree.get_db", return_value=db):
            response = client.get("/tree/unsaved", headers={"Authorization": "Bearer token"})

        assert response.status_code == 200
        result = response.json()

        # Should detect NO unsaved changes after normalization
        assert not result["unsaved"]


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "--tb=short"])
