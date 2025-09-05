#!/usr/bin/env python3
"""Debug script to list all registered routes"""

from app.main import app


def main():
    print("=== All registered routes ===")
    for route in app.routes:
        if hasattr(route, "methods") and hasattr(route, "path"):
            print(f"{list(route.methods)} {route.path}")

    print("\n=== Looking for invite-related routes ===")
    for route in app.routes:
        if hasattr(route, "path") and "invite" in route.path.lower():
            print(f"{list(route.methods)} {route.path}")


if __name__ == "__main__":
    main()
