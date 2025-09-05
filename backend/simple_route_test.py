#!/usr/bin/env python3
"""Test script to check if the delete route is accessible"""


def test_route_registration():
    """Test if the delete route is properly registered"""
    from fastapi.testclient import TestClient

    from app.main import app

    client = TestClient(app)

    # Check if any route exists at all
    print("Testing /healthz:")
    response = client.get("/healthz")
    print(f"  Status: {response.status_code}")

    # Test the delete endpoint
    print("Testing DELETE /auth/invites/test:")
    response = client.delete("/auth/invites/test")
    print(f"  Status: {response.status_code}")
    print(f"  Response: {response.text}")

    # Test with authentication header
    print("Testing DELETE /auth/invites/test with fake auth:")
    headers = {"Authorization": "Bearer fake-token"}
    response = client.delete("/auth/invites/test", headers=headers)
    print(f"  Status: {response.status_code}")
    print(f"  Response: {response.text}")


if __name__ == "__main__":
    test_route_registration()
