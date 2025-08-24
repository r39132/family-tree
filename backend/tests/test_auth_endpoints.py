from fastapi.testclient import TestClient
from app.main import app
from app.firestore_client import get_db as real_get_db
from app.deps import get_current_username
from app.auth_utils import hash_password, create_reset_token, decode_token
from google.cloud import firestore
import app.routes_auth as routes_auth
import app.routes_tree as routes_tree
from tests.test_tree_endpoints import FakeDB, fake_db


def setup_module(module):
    # Override auth and db for all tests in this module
    module._orig_db = app.dependency_overrides.get(real_get_db)
    module._orig_user = app.dependency_overrides.get(get_current_username)
    app.dependency_overrides[real_get_db] = lambda: fake_db
    app.dependency_overrides[get_current_username] = lambda: "tester"
    # Monkeypatch direct imports used inside route modules
    module._orig_tree_get_db = routes_tree.get_db
    module._orig_auth_get_db = routes_auth.get_db
    routes_tree.get_db = lambda: fake_db
    routes_auth.get_db = lambda: fake_db


def teardown_module(module):
    if module._orig_db is not None:
        app.dependency_overrides[real_get_db] = module._orig_db
    if module._orig_user is not None:
        app.dependency_overrides[get_current_username] = module._orig_user
    # restore monkeypatches
    routes_tree.get_db = module._orig_tree_get_db
    routes_auth.get_db = module._orig_auth_get_db


def setup_function(function):
    # Reset fake DB state before each test to prevent cross-test interference
    fake_db._store.clear()
    fake_db._store.update({
        "members": {},
        "relations": {},
        "member_keys": {},
        "invites": {},
        "users": {},
    })


def test_register_without_invite_when_required():
    """Test registration fails when invite is required but not provided"""
    client = TestClient(app)
    r = client.post("/auth/register", json={
        "username": "newuser",
        "email": "new@test.com", 
        "password": "password123",
        "confirm_password": "password123",
        "invite_code": "invalid-code"
    })
    assert r.status_code == 400
    assert "Invalid invite code" in r.json()["detail"]


def test_register_duplicate_username():
    """Test registration fails with duplicate username"""
    client = TestClient(app)
    # Create existing user
    fake_db.collection("users").document("existing").set({
        "email": "existing@test.com",
        "password_hash": hash_password("password")
    })
    
    r = client.post("/auth/register", json={
        "username": "existing",
        "email": "new@test.com",
        "password": "password123", 
        "confirm_password": "password123",
        "invite_code": "any"
    })
    assert r.status_code == 400
    assert "Username already exists" in r.json()["detail"]


def test_login_invalid_user():
    """Test login with non-existent user"""
    client = TestClient(app)
    r = client.post("/auth/login", json={
        "username": "nonexistent",
        "password": "password"
    })
    assert r.status_code == 401
    assert "Invalid credentials" in r.json()["detail"]


def test_login_invalid_password():
    """Test login with wrong password"""
    client = TestClient(app)
    # Create user
    fake_db.collection("users").document("testuser").set({
        "email": "test@test.com",
        "password_hash": hash_password("correctpassword")
    })
    
    r = client.post("/auth/login", json={
        "username": "testuser", 
        "password": "wrongpassword"
    })
    assert r.status_code == 401
    assert "Invalid credentials" in r.json()["detail"]


def test_login_success():
    """Test successful login"""
    client = TestClient(app)
    # Create user
    fake_db.collection("users").document("testuser").set({
        "email": "test@test.com",
        "password_hash": hash_password("correctpassword")
    })
    
    r = client.post("/auth/login", json={
        "username": "testuser",
        "password": "correctpassword"
    })
    assert r.status_code == 200
    assert "access_token" in r.json()


def test_reset_password():
    """Test password reset flow"""
    client = TestClient(app)
    # Create user
    fake_db.collection("users").document("testuser").set({
        "email": "test@test.com", 
        "password_hash": hash_password("oldpassword")
    })
    
    # Generate reset token
    token = create_reset_token("testuser")
    
    # Reset password
    r = client.post("/auth/reset", json={
        "username": "testuser",
        "token": token,
        "new_password": "newpassword123",
        "confirm_password": "newpassword123"
    })
    assert r.status_code == 200
    assert r.json()["ok"] is True


def test_reset_password_mismatch():
    """Test password reset with mismatched passwords"""
    client = TestClient(app)
    token = create_reset_token("testuser")
    
    r = client.post("/auth/reset", json={
        "username": "testuser",
        "token": token, 
        "new_password": "newpassword123",
        "confirm_password": "differentpassword"
    })
    assert r.status_code == 400
    assert "Passwords do not match" in r.json()["detail"]


def test_reset_password_invalid_token():
    """Test password reset with invalid token"""
    client = TestClient(app)
    
    r = client.post("/auth/reset", json={
        "username": "testuser",
        "token": "invalid-token",
        "new_password": "newpassword123", 
        "confirm_password": "newpassword123"
    })
    assert r.status_code == 400
    assert "Invalid or expired token" in r.json()["detail"]


def test_reset_password_nonexistent_user():
    """Test password reset for non-existent user"""
    client = TestClient(app)
    token = create_reset_token("nonexistent")
    
    r = client.post("/auth/reset", json={
        "username": "nonexistent",
        "token": token,
        "new_password": "newpassword123",
        "confirm_password": "newpassword123"
    })
    assert r.status_code == 400
    assert "User not found" in r.json()["detail"]


def test_create_invite_invalid_count():
    """Test creating invites with invalid count"""
    client = TestClient(app)
    
    # Test count too low
    r = client.post("/auth/invite?count=0", headers={"Authorization": "Bearer x"})
    assert r.status_code == 400
    assert "count must be between 1 and 10" in r.json()["detail"]
    
    # Test count too high
    r = client.post("/auth/invite?count=11", headers={"Authorization": "Bearer x"})
    assert r.status_code == 400
    assert "count must be between 1 and 10" in r.json()["detail"]


def test_test_email_endpoint():
    """Test the test email endpoint"""
    client = TestClient(app)
    
    r = client.post("/auth/test-email?to=test@example.com")
    assert r.status_code == 200
    assert r.json()["ok"] is True
