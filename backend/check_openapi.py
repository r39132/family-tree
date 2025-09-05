#!/usr/bin/env python3
"""Check OpenAPI schema for routes"""

from app.main import app


def main():
    openapi_schema = app.openapi()

    print("=== Checking OpenAPI schema for invite routes ===")

    paths = openapi_schema.get("paths", {})

    for path, methods in paths.items():
        if "invite" in path.lower():
            print(f"Path: {path}")
            for method, details in methods.items():
                print(f"  {method.upper()}: {details.get('summary', 'No summary')}")

    # Check specifically for the delete route
    delete_route = "/auth/invites/{code}"
    if delete_route in paths:
        print(f"\n✓ Found delete route: {delete_route}")
        if "delete" in paths[delete_route]:
            print("✓ DELETE method is available")
        else:
            print("✗ DELETE method is missing")
            print(f"Available methods: {list(paths[delete_route].keys())}")
    else:
        print(f"\n✗ Delete route {delete_route} not found in OpenAPI schema")
        print("Available paths with 'invite':")
        for path in paths.keys():
            if "invite" in path.lower():
                print(f"  {path}")


if __name__ == "__main__":
    main()
