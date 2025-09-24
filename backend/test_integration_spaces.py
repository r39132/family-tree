"""
Integration tests for space-specific functionality.
Tests full-stack operations with real API calls and space isolation.
"""

import os
import time
from typing import Dict

import pytest
import requests

# Test configuration
BASE_URL = os.getenv("TEST_API_URL", "http://localhost:8000")
TEST_TIMEOUT = 10


class TestSpaceIntegration:
    """Integration tests for space isolation across the full stack"""

    def setup_method(self):
        """Setup test data and authenticate test users"""
        self.test_spaces = {
            "space_a": {
                "id": f"test_space_a_{int(time.time())}",
                "name": "Test Family A",
                "users": [],
            },
            "space_b": {
                "id": f"test_space_b_{int(time.time())}",
                "name": "Test Family B",
                "users": [],
            },
        }

        # Test tokens would be obtained through proper authentication
        # For now using placeholder tokens
        self.tokens = {"user_a": "test_token_user_a", "user_b": "test_token_user_b"}

        # In a real test environment, you would:
        # 1. Create test user accounts
        # 2. Create test family spaces
        # 3. Assign users to spaces
        # 4. Obtain authentication tokens

    def get_headers(self, user: str) -> Dict[str, str]:
        """Get headers for authenticated requests"""
        return {"Authorization": f"Bearer {self.tokens[user]}", "Content-Type": "application/json"}

    def test_tree_endpoint_space_isolation(self):
        """Test that /tree endpoint returns only user's space data"""

        # Create test members in space A
        space_a_member = {
            "first_name": "Alice",
            "last_name": "TestUser",
            "dob": "1990-01-01",
            "gender": "Female",
        }

        try:
            # User A creates member in their space
            response = requests.post(
                f"{BASE_URL}/api/tree/members",
                headers=self.get_headers("user_a"),
                json=space_a_member,
                timeout=TEST_TIMEOUT,
            )

            if response.status_code == 401:
                pytest.skip("Authentication not configured for integration tests")

            assert response.status_code == 200

            # Create test members in space B
            space_b_member = {
                "first_name": "Bob",
                "last_name": "TestUser",
                "dob": "1985-01-01",
                "gender": "Male",
            }

            response = requests.post(
                f"{BASE_URL}/api/tree/members",
                headers=self.get_headers("user_b"),
                json=space_b_member,
                timeout=TEST_TIMEOUT,
            )
            assert response.status_code == 200

            # User A requests tree data
            response = requests.get(
                f"{BASE_URL}/api/tree", headers=self.get_headers("user_a"), timeout=TEST_TIMEOUT
            )
            assert response.status_code == 200
            tree_a_data = response.json()

            # Should only see space A member
            member_names = [m["first_name"] for m in tree_a_data.get("members", [])]
            assert "Alice" in member_names
            assert "Bob" not in member_names  # Should not see space B data

            # User B requests tree data
            response = requests.get(
                f"{BASE_URL}/api/tree", headers=self.get_headers("user_b"), timeout=TEST_TIMEOUT
            )
            assert response.status_code == 200
            tree_b_data = response.json()

            # Should only see space B member
            member_names = [m["first_name"] for m in tree_b_data.get("members", [])]
            assert "Bob" in member_names
            assert "Alice" not in member_names  # Should not see space A data

        except requests.exceptions.RequestException:
            pytest.skip("API server not available for integration tests")

    def test_version_save_and_recovery_space_isolation(self):
        """Test that version save/recovery maintains space isolation"""

        try:
            # User A saves their tree state
            response = requests.post(
                f"{BASE_URL}/api/tree/save",
                headers=self.get_headers("user_a"),
                timeout=TEST_TIMEOUT,
            )

            if response.status_code == 401:
                pytest.skip("Authentication not configured for integration tests")

            assert response.status_code == 200
            version_a_data = response.json()
            version_a_id = version_a_data["id"]

            # User B saves their tree state
            response = requests.post(
                f"{BASE_URL}/api/tree/save",
                headers=self.get_headers("user_b"),
                timeout=TEST_TIMEOUT,
            )
            assert response.status_code == 200
            version_b_data = response.json()
            version_b_id = version_b_data["id"]

            # User A attempts to recover User B's version (should fail)
            response = requests.post(
                f"{BASE_URL}/api/tree/recover",
                headers=self.get_headers("user_a"),
                json={"version_id": version_b_id},
                timeout=TEST_TIMEOUT,
            )

            # Should reject cross-space recovery
            assert response.status_code == 403
            assert "different space" in response.json()["detail"].lower()

            # User A can recover their own version (should succeed)
            response = requests.post(
                f"{BASE_URL}/api/tree/recover",
                headers=self.get_headers("user_a"),
                json={"version_id": version_a_id},
                timeout=TEST_TIMEOUT,
            )
            assert response.status_code == 200

            # User B can recover their own version (should succeed)
            response = requests.post(
                f"{BASE_URL}/api/tree/recover",
                headers=self.get_headers("user_b"),
                json={"version_id": version_b_id},
                timeout=TEST_TIMEOUT,
            )
            assert response.status_code == 200

        except requests.exceptions.RequestException:
            pytest.skip("API server not available for integration tests")

    def test_versions_list_space_filtering(self):
        """Test that /versions endpoint only returns user's space versions"""

        try:
            # User A saves multiple versions
            for i in range(3):
                response = requests.post(
                    f"{BASE_URL}/api/tree/save",
                    headers=self.get_headers("user_a"),
                    timeout=TEST_TIMEOUT,
                )

                if response.status_code == 401:
                    pytest.skip("Authentication not configured for integration tests")

                assert response.status_code == 200
                time.sleep(0.5)  # Ensure different timestamps

            # User B saves multiple versions
            for i in range(2):
                response = requests.post(
                    f"{BASE_URL}/api/tree/save",
                    headers=self.get_headers("user_b"),
                    timeout=TEST_TIMEOUT,
                )
                assert response.status_code == 200
                time.sleep(0.5)

            # User A requests versions list
            response = requests.get(
                f"{BASE_URL}/api/tree/versions",
                headers=self.get_headers("user_a"),
                timeout=TEST_TIMEOUT,
            )
            assert response.status_code == 200
            versions_a = response.json()

            # Should see 3 versions for User A
            assert len(versions_a) == 3

            # User B requests versions list
            response = requests.get(
                f"{BASE_URL}/api/tree/versions",
                headers=self.get_headers("user_b"),
                timeout=TEST_TIMEOUT,
            )
            assert response.status_code == 200
            versions_b = response.json()

            # Should see 2 versions for User B
            assert len(versions_b) == 2

            # Version IDs should be completely different
            version_ids_a = {v["id"] for v in versions_a}
            version_ids_b = {v["id"] for v in versions_b}
            assert len(version_ids_a.intersection(version_ids_b)) == 0

        except requests.exceptions.RequestException:
            pytest.skip("API server not available for integration tests")

    def test_unsaved_changes_space_specific_active_versions(self):
        """Test that unsaved changes detection uses space-specific active versions"""

        try:
            # User A saves initial state
            response = requests.post(
                f"{BASE_URL}/api/tree/save",
                headers=self.get_headers("user_a"),
                timeout=TEST_TIMEOUT,
            )

            if response.status_code == 401:
                pytest.skip("Authentication not configured for integration tests")

            assert response.status_code == 200

            # Check unsaved status immediately after save
            response = requests.get(
                f"{BASE_URL}/api/tree/unsaved",
                headers=self.get_headers("user_a"),
                timeout=TEST_TIMEOUT,
            )
            assert response.status_code == 200
            unsaved_data = response.json()
            assert not unsaved_data["unsaved"]  # Should be saved

            # User B saves their state (should not affect User A)
            response = requests.post(
                f"{BASE_URL}/api/tree/save",
                headers=self.get_headers("user_b"),
                timeout=TEST_TIMEOUT,
            )
            assert response.status_code == 200

            # User A's unsaved status should remain unchanged
            response = requests.get(
                f"{BASE_URL}/api/tree/unsaved",
                headers=self.get_headers("user_a"),
                timeout=TEST_TIMEOUT,
            )
            assert response.status_code == 200
            unsaved_data = response.json()
            assert not unsaved_data["unsaved"]  # Still saved for User A

            # User A makes changes (create new member)
            new_member = {
                "first_name": "NewMember",
                "last_name": "TestUser",
                "dob": "2000-01-01",
                "gender": "Other",
            }

            response = requests.post(
                f"{BASE_URL}/api/tree/members",
                headers=self.get_headers("user_a"),
                json=new_member,
                timeout=TEST_TIMEOUT,
            )
            assert response.status_code == 200

            # Now User A should have unsaved changes
            response = requests.get(
                f"{BASE_URL}/api/tree/unsaved",
                headers=self.get_headers("user_a"),
                timeout=TEST_TIMEOUT,
            )
            assert response.status_code == 200
            unsaved_data = response.json()
            assert unsaved_data["unsaved"]  # Should now be unsaved

            # User B's status should be unaffected
            response = requests.get(
                f"{BASE_URL}/api/tree/unsaved",
                headers=self.get_headers("user_b"),
                timeout=TEST_TIMEOUT,
            )
            assert response.status_code == 200
            unsaved_data = response.json()
            assert not unsaved_data["unsaved"]  # Still saved for User B

        except requests.exceptions.RequestException:
            pytest.skip("API server not available for integration tests")

    def test_concurrent_operations_space_isolation(self):
        """Test that concurrent operations by different users don't interfere"""

        try:
            import threading
            import time

            results = {"user_a": [], "user_b": []}

            def save_multiple_versions(user: str, count: int):
                """Save multiple versions for a user"""
                for i in range(count):
                    try:
                        response = requests.post(
                            f"{BASE_URL}/api/tree/save",
                            headers=self.get_headers(user),
                            timeout=TEST_TIMEOUT,
                        )
                        results[user].append(
                            {
                                "status": response.status_code,
                                "data": response.json() if response.status_code == 200 else None,
                            }
                        )
                        time.sleep(0.1)  # Small delay between saves
                    except Exception as e:
                        results[user].append({"error": str(e)})

            # Start concurrent operations
            thread_a = threading.Thread(target=save_multiple_versions, args=("user_a", 5))
            thread_b = threading.Thread(target=save_multiple_versions, args=("user_b", 5))

            thread_a.start()
            thread_b.start()

            thread_a.join(timeout=30)
            thread_b.join(timeout=30)

            if not results["user_a"] or not results["user_b"]:
                pytest.skip("Authentication not configured for integration tests")

            # All operations should succeed
            assert all(r.get("status") == 200 for r in results["user_a"])
            assert all(r.get("status") == 200 for r in results["user_b"])

            # Version numbers should be sequential within each space
            versions_a = [r["data"]["version"] for r in results["user_a"]]
            versions_b = [r["data"]["version"] for r in results["user_b"]]

            # Each space should have sequential version numbers
            assert versions_a == list(range(1, len(versions_a) + 1))
            assert versions_b == list(range(1, len(versions_b) + 1))

        except (requests.exceptions.RequestException, ImportError):
            pytest.skip("API server not available or threading not supported for integration tests")

    def teardown_method(self):
        """Cleanup test data"""
        # In a real test environment, you would clean up:
        # 1. Delete test members
        # 2. Delete test versions
        # 3. Delete test spaces
        # 4. Delete test user accounts
        pass


class TestSpaceConsistencyValidation:
    """Integration tests for data consistency across space operations"""

    def setup_method(self):
        """Setup test environment"""
        self.base_url = BASE_URL
        self.test_token = "test_token"

    def get_headers(self) -> Dict[str, str]:
        """Get headers for authenticated requests"""
        return {"Authorization": f"Bearer {self.test_token}", "Content-Type": "application/json"}

    def test_member_creation_includes_space_id(self):
        """Test that created members include proper space_id"""

        try:
            member_data = {
                "first_name": "SpaceTest",
                "last_name": "Member",
                "dob": "1995-01-01",
                "gender": "Other",
            }

            response = requests.post(
                f"{self.base_url}/api/tree/members",
                headers=self.get_headers(),
                json=member_data,
                timeout=TEST_TIMEOUT,
            )

            if response.status_code == 401:
                pytest.skip("Authentication not configured for integration tests")

            assert response.status_code == 200
            created_member = response.json()

            # Should include space_id in response
            assert "space_id" in created_member
            assert created_member["space_id"] is not None
            assert len(created_member["space_id"]) > 0

            # Verify member appears in tree
            response = requests.get(
                f"{self.base_url}/api/tree", headers=self.get_headers(), timeout=TEST_TIMEOUT
            )
            assert response.status_code == 200
            tree_data = response.json()

            # Should find the created member
            member_names = [m["first_name"] for m in tree_data.get("members", [])]
            assert "SpaceTest" in member_names

        except requests.exceptions.RequestException:
            pytest.skip("API server not available for integration tests")

    def test_relations_maintain_space_consistency(self):
        """Test that relation operations maintain space_id consistency"""

        try:
            # Create parent member
            parent_data = {
                "first_name": "ParentTest",
                "last_name": "Member",
                "dob": "1980-01-01",
                "gender": "Other",
            }

            response = requests.post(
                f"{self.base_url}/api/tree/members",
                headers=self.get_headers(),
                json=parent_data,
                timeout=TEST_TIMEOUT,
            )

            if response.status_code == 401:
                pytest.skip("Authentication not configured for integration tests")

            assert response.status_code == 200
            parent = response.json()

            # Create child member
            child_data = {
                "first_name": "ChildTest",
                "last_name": "Member",
                "dob": "2010-01-01",
                "gender": "Other",
            }

            response = requests.post(
                f"{self.base_url}/api/tree/members",
                headers=self.get_headers(),
                json=child_data,
                timeout=TEST_TIMEOUT,
            )
            assert response.status_code == 200
            child = response.json()

            # Create parent-child relationship
            move_data = {"child_id": child["id"], "new_parent_id": parent["id"]}

            response = requests.post(
                f"{self.base_url}/api/tree/move",
                headers=self.get_headers(),
                json=move_data,
                timeout=TEST_TIMEOUT,
            )
            assert response.status_code == 200

            # Verify relationship appears in tree
            response = requests.get(
                f"{self.base_url}/api/tree", headers=self.get_headers(), timeout=TEST_TIMEOUT
            )
            assert response.status_code == 200
            tree_data = response.json()

            # Should show hierarchical relationship
            assert len(tree_data.get("roots", [])) > 0

            # Both members should have the same space_id
            members = tree_data.get("members", [])
            parent_member = next(m for m in members if m["first_name"] == "ParentTest")
            child_member = next(m for m in members if m["first_name"] == "ChildTest")

            assert parent_member["space_id"] == child_member["space_id"]

        except requests.exceptions.RequestException:
            pytest.skip("API server not available for integration tests")


if __name__ == "__main__":
    # Run integration tests
    pytest.main([__file__, "-v", "-s", "--tb=short"])
