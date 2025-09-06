#!/usr/bin/env python3

import sys

sys.path.append("/Users/r39132/Projects/family-tree/backend")

from unittest.mock import patch

from fastapi.testclient import TestClient

from app.firestore_client import get_db as real_get_db
from app.main import app
from tests.test_tree_endpoints import fake_db

# Setup
app.dependency_overrides[real_get_db] = lambda: fake_db

# Clear and setup fake db
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

# Add user
fake_db._store["users"]["testuser"] = {"email": "test@example.com", "password_hash": "hash"}

client = TestClient(app)

payload = {"username": "testuser", "email": "test@example.com"}

with patch("app.routes_auth.send_mail") as mock_send_mail:
    response = client.post("/auth/forgot", json=payload)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
