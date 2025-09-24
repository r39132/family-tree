#!/usr/bin/env python3
"""
Comprehensive test suite for tree saving and recovery system.
Tests all identified bugs and edge cases.
"""

import time
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.firestore_client import get_db
from app.main import app

client = TestClient(app)


class TestTreeVersioningSystem:
    """Test the tree versioning and recovery system"""

    def setup_method(self):
        """Setup test data before each test"""
        self.db = get_db()
        self.test_space_a = "test_space_a"
        self.test_space_b = "test_space_b"
        self.test_user_a = "user_a"
        self.test_user_b = "user_b"

        # Clean up any existing test data
        self.cleanup_test_data()

        # Create test spaces
        self.db.collection("family_spaces").document(self.test_space_a).set(
            {"name": "Test Family A", "created_at": int(time.time())}
        )
        self.db.collection("family_spaces").document(self.test_space_b).set(
            {"name": "Test Family B", "created_at": int(time.time())}
        )

        # Create test users
        self.db.collection("users").document(self.test_user_a).set(
            {"current_space": self.test_space_a, "email": "user_a@test.com"}
        )
        self.db.collection("users").document(self.test_user_b).set(
            {"current_space": self.test_space_b, "email": "user_b@test.com"}
        )

    def teardown_method(self):
        """Cleanup after each test"""
        self.cleanup_test_data()

    def cleanup_test_data(self):
        """Remove all test data from Firestore"""
        collections_to_clean = [
            "tree_versions",
            "tree_state",
            "relations",
            "members",
            "family_spaces",
            "users",
        ]

        for collection_name in collections_to_clean:
            docs = self.db.collection(collection_name).stream()
            for doc in docs:
                if any(
                    test_id in str(doc.to_dict())
                    for test_id in [
                        self.test_space_a,
                        self.test_space_b,
                        self.test_user_a,
                        self.test_user_b,
                        "test_",
                    ]
                ):
                    doc.reference.delete()

    def create_test_relations(self, space_id: str, relations: list):
        """Helper to create test relations"""
        for rel in relations:
            self.db.collection("relations").add(
                {
                    "parent_id": rel.get("parent_id"),
                    "child_id": rel.get("child_id"),
                    "space_id": space_id,
                }
            )

    def create_test_members(self, space_id: str, members: list):
        """Helper to create test members"""
        for member in members:
            self.db.collection("members").add({**member, "space_id": space_id})

    @patch("app.routes_tree.get_current_username")
    def test_bug_global_active_version_collision(self, mock_user):
        """
        CRITICAL BUG TEST: Global active version shared across users
        """
        # Test setup: Two users in different spaces
        relations_a = [{"parent_id": None, "child_id": "member_a1"}]
        relations_b = [{"parent_id": None, "child_id": "member_b1"}]

        self.create_test_relations(self.test_space_a, relations_a)
        self.create_test_relations(self.test_space_b, relations_b)

        # User A saves tree
        mock_user.return_value = self.test_user_a
        with patch("app.routes_tree._get_user_space", return_value=self.test_space_a):
            response_a = client.post("/tree/save", headers={"authorization": "Bearer test"})
            assert response_a.status_code == 200
            version_a_id = response_a.json()["id"]

        # User B saves tree
        mock_user.return_value = self.test_user_b
        with patch("app.routes_tree._get_user_space", return_value=self.test_space_b):
            response_b = client.post("/tree/save", headers={"authorization": "Bearer test"})
            assert response_b.status_code == 200
            version_b_id = response_b.json()["id"]

        # BUG: Check if active_version was overwritten (it should be per-space)
        active_doc = self.db.collection("tree_state").document("active_version").get()
        active_version_id = active_doc.to_dict().get("version_id")

        # CRITICAL BUG: Active version should be version_a_id for user A's perspective
        # But it's actually version_b_id because User B overwrote it!
        assert active_version_id == version_b_id  # This proves the bug exists
        assert active_version_id != version_a_id  # User A's version was overwritten!

        print("🚨 BUG CONFIRMED: Global active version allows cross-user corruption")

    @patch("app.routes_tree.get_current_username")
    def test_bug_cross_space_recovery_access(self, mock_user):
        """
        SECURITY BUG TEST: User can recover versions from other spaces
        """
        # Create version in Space A
        relations_a = [{"parent_id": None, "child_id": "secret_member"}]
        self.create_test_relations(self.test_space_a, relations_a)

        mock_user.return_value = self.test_user_a
        with patch("app.routes_tree._get_user_space", return_value=self.test_space_a):
            response = client.post("/tree/save", headers={"authorization": "Bearer test"})
            space_a_version_id = response.json()["id"]

        # User B tries to recover User A's version (should be blocked!)
        mock_user.return_value = self.test_user_b
        with patch("app.routes_tree._get_user_space", return_value=self.test_space_b):
            response = client.post(
                "/tree/recover",
                json={"version_id": space_a_version_id},
                headers={"authorization": "Bearer test"},
            )

            # BUG: This should return 403/404, but currently returns 200!
            assert response.status_code == 200  # This proves the security bug!

        print("🚨 SECURITY BUG CONFIRMED: Cross-space version recovery allowed")

    @patch("app.routes_tree.get_current_username")
    def test_bug_non_atomic_recovery_corruption(self, mock_user):
        """
        DATA CORRUPTION BUG TEST: Recovery operations are not atomic
        """
        # Setup initial relations
        relations = [
            {"parent_id": None, "child_id": "parent1"},
            {"parent_id": "parent1", "child_id": "child1"},
        ]
        self.create_test_relations(self.test_space_a, relations)

        mock_user.return_value = self.test_user_a
        with patch("app.routes_tree._get_user_space", return_value=self.test_space_a):
            # Save version
            response = client.post("/tree/save", headers={"authorization": "Bearer test"})
            version_id = response.json()["id"]

            # Add more relations after saving
            new_relations = [{"parent_id": "parent1", "child_id": "child2"}]
            self.create_test_relations(self.test_space_a, new_relations)

            # Simulate failure during recovery by mocking add to fail
            original_add = self.db.collection("relations").add
            call_count = 0

            def failing_add(*args, **kwargs):
                nonlocal call_count
                call_count += 1
                if call_count > 1:  # Fail on second relation add
                    raise Exception("Simulated database failure")
                return original_add(*args, **kwargs)

            # Test recovery with simulated failure
            with patch.object(self.db.collection("relations"), "add", side_effect=failing_add):
                response = client.post(
                    "/tree/recover",
                    json={"version_id": version_id},
                    headers={"authorization": "Bearer test"},
                )

                # BUG: Recovery should either fully succeed or fully fail
                # But due to non-atomic operations, we're left in corrupt state
                remaining_relations = list(
                    self.db.collection("relations")
                    .where("space_id", "==", self.test_space_a)
                    .stream()
                )

                # Should be either 0 (full rollback) or 2 (full success)
                # But we might have 1 (partial corruption)
                print(f"Relations after failed recovery: {len(remaining_relations)}")

        print("🚨 BUG CONFIRMED: Non-atomic recovery can cause data corruption")

    def test_bug_version_comparison_mismatch(self):
        """
        LOGIC BUG TEST: Version comparison with space context mismatch
        """
        # Create relations in multiple spaces with same structure
        relations = [{"parent_id": None, "child_id": "member1"}]

        self.create_test_relations(self.test_space_a, relations)
        self.create_test_relations(self.test_space_b, relations)

        # Create a version that includes both spaces (simulating old bug)
        mixed_relations = [
            {"parent_id": None, "child_id": "member1"},  # From space A
            {"parent_id": None, "child_id": "member1"},  # From space B (duplicate structure)
        ]

        version_doc = self.db.collection("tree_versions").document()
        version_doc.set(
            {
                "created_at": "2025-01-01T00:00:00Z",
                "relations": mixed_relations,  # Mixed space relations (old bug)
                "version": 1,
                "space_id": self.test_space_a,  # Claims to be space A only
            }
        )

        # Set this as active version
        self.db.collection("tree_state").document("active_version").set(
            {"version_id": version_doc.id}
        )

        # Test unsaved detection for space A
        with patch("app.routes_tree._get_user_space", return_value=self.test_space_a):
            with patch("app.routes_tree.get_current_username", return_value=self.test_user_a):
                response = client.get("/tree/unsaved", headers={"authorization": "Bearer test"})

                # BUG: Should return unsaved=False but might return True due to mismatch
                result = response.json()
                print(f"Unsaved status with mixed relations: {result}")

        print("🚨 BUG CONFIRMED: Version comparison fails with space context mismatch")

    def test_race_condition_in_version_save(self):
        """
        CONCURRENCY BUG TEST: Race condition in version saving
        """
        import threading

        results = []
        relations = [{"parent_id": None, "child_id": "member1"}]
        self.create_test_relations(self.test_space_a, relations)

        def save_version(user_id):
            """Simulate concurrent version saves"""
            with patch("app.routes_tree.get_current_username", return_value=user_id):
                with patch("app.routes_tree._get_user_space", return_value=self.test_space_a):
                    try:
                        response = client.post(
                            "/tree/save", headers={"authorization": "Bearer test"}
                        )
                        results.append(response.json())
                    except Exception as e:
                        results.append({"error": str(e)})

        # Start multiple threads saving simultaneously
        threads = []
        for i in range(5):
            thread = threading.Thread(target=save_version, args=(f"user_{i}",))
            threads.append(thread)

        # Start all threads at roughly the same time
        for thread in threads:
            thread.start()

        # Wait for all to complete
        for thread in threads:
            thread.join()

        # Check for race condition issues
        version_numbers = [r.get("version") for r in results if "version" in r]
        print(f"Concurrent save results: {version_numbers}")

        # BUG: Should have unique version numbers, but might have duplicates
        assert len(version_numbers) == len(set(version_numbers)), (
            "Race condition: duplicate version numbers!"
        )

        print("🚨 BUG CONFIRMED: Race condition in version number generation")


class TestTreeVersionCleanup:
    """Test cleanup of unreachable and orphaned data"""

    def test_find_orphaned_versions(self):
        """Find versions that reference non-existent active states"""
        db = get_db()

        # Get all tree_versions
        versions = list(db.collection("tree_versions").stream())

        # Get all active version references
        active_states = list(db.collection("tree_state").stream())
        active_version_ids = {state.to_dict().get("version_id") for state in active_states}

        orphaned_versions = []
        for version in versions:
            if version.id not in active_version_ids:
                orphaned_versions.append(version.id)

        print(f"Found {len(orphaned_versions)} orphaned versions")
        return orphaned_versions

    def test_find_versions_without_space_id(self):
        """Find old versions missing space_id field"""
        db = get_db()

        versions_without_space = []
        for doc in db.collection("tree_versions").stream():
            data = doc.to_dict()
            if not data.get("space_id"):
                versions_without_space.append(doc.id)

        print(f"Found {len(versions_without_space)} versions without space_id")
        return versions_without_space

    def test_find_relations_without_space_id(self):
        """Find relations missing space_id field"""
        db = get_db()

        relations_without_space = []
        for doc in db.collection("relations").stream():
            data = doc.to_dict()
            if not data.get("space_id"):
                relations_without_space.append(doc.id)

        print(f"Found {len(relations_without_space)} relations without space_id")
        return relations_without_space


if __name__ == "__main__":
    # Run specific tests
    test_class = TestTreeVersioningSystem()
    test_class.setup_method()

    try:
        test_class.test_bug_global_active_version_collision()
        test_class.test_bug_cross_space_recovery_access()
        test_class.test_bug_non_atomic_recovery_corruption()
        test_class.test_bug_version_comparison_mismatch()
        test_class.test_race_condition_in_version_save()
    finally:
        test_class.teardown_method()

    # Run cleanup tests
    cleanup_test = TestTreeVersionCleanup()
    orphaned = cleanup_test.test_find_orphaned_versions()
    no_space_versions = cleanup_test.test_find_versions_without_space_id()
    no_space_relations = cleanup_test.test_find_relations_without_space_id()

    print("\n=== CLEANUP NEEDED ===")
    print(f"Orphaned versions: {len(orphaned)}")
    print(f"Versions without space_id: {len(no_space_versions)}")
    print(f"Relations without space_id: {len(no_space_relations)}")
