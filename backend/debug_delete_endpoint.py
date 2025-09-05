#!/usr/bin/env python3
"""Quick test to debug the delete invite endpoint authentication issue"""

from fastapi.testclient import TestClient

from app.main import app


def main():
    client = TestClient(app)

    print("=== Testing DELETE /auth/invites/test-code without auth ===")
    response = client.delete("/auth/invites/test-code")
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json() if response.status_code != 422 else response.text}")

    print("\n=== Testing DELETE /auth/invites/test-code with fake auth ===")
    headers = {"Authorization": "Bearer fake-token"}
    response = client.delete("/auth/invites/test-code", headers=headers)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json() if response.status_code != 422 else response.text}")

    print("\n=== Testing if endpoint exists by checking routes ===")
    # Check if the route is registered
    for route in app.routes:
        if hasattr(route, "path") and "invites" in route.path:
            print(f"Route: {route.methods} {route.path}")


if __name__ == "__main__":
    main()
