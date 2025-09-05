#!/usr/bin/env python3

try:
    print("Importing app...")
    from app.main import app

    print(f"✓ App imported successfully, has {len(app.routes)} routes")

    print("\nImporting auth router...")
    from app.routes_auth import router

    print(f"✓ Auth router imported successfully, has {len(router.routes)} routes")

    print("\nChecking for delete route in auth router...")
    for route in router.routes:
        if hasattr(route, "path") and "invites/{code}" in route.path:
            print(f"✓ Found route: {route.methods} {route.path}")

    print("\nChecking for delete route in main app...")
    for route in app.routes:
        if hasattr(route, "path") and "invites" in route.path:
            methods = getattr(route, "methods", ["Unknown"])
            print(f"Found invite route: {methods} {route.path}")

    print("\nTesting endpoint with TestClient...")
    from fastapi.testclient import TestClient

    client = TestClient(app)
    response = client.delete("/auth/invites/test-code")
    print(f"DELETE /auth/invites/test-code returned: {response.status_code}")

except Exception as e:
    print(f"✗ Error: {e}")
    import traceback

    traceback.print_exc()
