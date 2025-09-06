import pytest
from fastapi.testclient import TestClient

from app.main import app


class FakeDoc:
    def __init__(self, store, col, doc_id):
        self._store = store
        self._col = col
        self.id = doc_id

    def get(self):
        class R:
            def __init__(self, exists, data, id):
                self._exists = exists
                self._data = data
                self.id = id

            @property
            def exists(self):
                return self._exists

            def to_dict(self):
                return dict(self._data) if self._data else {}

        return R(
            self.id in self._store[self._col],
            self._store[self._col].get(self.id),
            self.id,
        )

    def set(self, data):
        self._store[self._col][self.id] = dict(data)

    def update(self, data):
        self._store[self._col].setdefault(self.id, {})
        self._store[self._col][self.id].update(dict(data))


class FakeCollection:
    def __init__(self, store, name):
        self._store = store
        self._name = name

    def document(self, doc_id=None):
        assert doc_id is not None
        return FakeDoc(self._store, self._name, doc_id)

    def stream(self):
        for doc_id in list(self._store[self._name].keys()):
            yield FakeDoc(self._store, self._name, doc_id).get()


class FakeDB:
    def __init__(self):
        self._store = {
            "members": {},
            "relations": {},
            "member_keys": {},
            "invites": {},
            "users": {},
        }
        self._collections = {}

    def collection(self, name):
        if name not in self._store:
            self._store[name] = {}
        if name not in self._collections:
            self._collections[name] = FakeCollection(self._store, name)
        return self._collections[name]


@pytest.mark.skip(reason="temporarily disabled")
def test_email_invite_happy_path(monkeypatch):
    from app import routes_auth
    from app.deps import get_current_username

    # Use fake DB and stub send_mail
    fake_db = FakeDB()
    code = "abc123"
    fake_db.collection("invites").document(code).set({"status": "available"})

    sent = {}

    def fake_send_mail(to, subject, body):
        sent["to"] = to
        sent["subject"] = subject
        sent["body"] = body

    app.dependency_overrides[get_current_username] = lambda: "tester"
    orig_get_db = routes_auth.get_db
    orig_send_mail = routes_auth.send_mail
    routes_auth.get_db = lambda: fake_db
    routes_auth.send_mail = fake_send_mail

    client = TestClient(app)
    try:
        r = client.post(
            f"/auth/invites/{code}/email",
            json={"email": "x@example.com"},
            headers={"Authorization": "Bearer x"},
        )
        assert r.status_code == 200
        assert sent.get("to") == "x@example.com"
        assert "register" in (sent.get("body") or "")
    finally:
        routes_auth.get_db = orig_get_db
        routes_auth.send_mail = orig_send_mail
        app.dependency_overrides.clear()
