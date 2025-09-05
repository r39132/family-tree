#!/usr/bin/env python3
"""Simple test to debug the route issue"""

from fastapi.testclient import TestClient

from app.main import app


def main():
    client = TestClient(app)

    print("=== Testing various endpoints to understand the routing ===")

    # Test a known working endpoint
    print("1. Testing /healthz")
    response = client.get("/healthz")
    print(f"   Status: {response.status_code}")

    # Test auth endpoints
    print("2. Testing /auth/register")
    response = client.post("/auth/register")
    print(f"   Status: {response.status_code}")

    # Test the problematic delete endpoint
    print("3. Testing DELETE /auth/invites/test-code")
    response = client.delete("/auth/invites/test-code")
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.text}")

    # Test if the path exists with different method
    print("4. Testing GET /auth/invites/test-code")
    response = client.get("/auth/invites/test-code")
    print(f"   Status: {response.status_code}")


if __name__ == "__main__":
    main()
