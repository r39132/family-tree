from fastapi.testclient import TestClient

from app.main import app


# Minimal fakes to avoid Firestore in tests
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

    def delete(self):
        self._store[self._col].pop(self.id, None)

    def create(self, data):
        if self.id in self._store[self._col]:
            # mimic AlreadyExists
            raise Exception("exists")
        self._store[self._col][self.id] = dict(data)


class FakeCollection:
    def __init__(self, store, name):
        self._store = store
        self._name = name
        self._counter = 1

    def document(self, doc_id=None):
        if doc_id is None:
            doc_id = f"auto_{self._counter}"
            self._counter += 1
        return FakeDoc(self._store, self._name, doc_id)

    def stream(self):
        for doc_id in list(self._store[self._name].keys()):
            yield FakeDoc(self._store, self._name, doc_id).get()

    def where(self, field, op, value):
        class Q:
            def __init__(self, store, name, f, v):
                self._store = store
                self._name = name
                self._f = f
                self._v = v

            def stream(self):
                for doc_id, data in list(self._store[self._name].items()):
                    if data.get(self._f) == self._v:
                        yield FakeDoc(self._store, self._name, doc_id).get()

            def get(self):
                return [d for d in self.stream()]

        return Q(self._store, self._name, field, value)

    def add(self, data):
        doc = self.document()
        doc.set(data)
        return doc


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


def test_create_member_rejects_future_dob():
    from app import routes_tree
    from app.deps import get_current_username

    fake_db = FakeDB()

    app.dependency_overrides[get_current_username] = lambda: "tester"
    orig_get_db = routes_tree.get_db
    routes_tree.get_db = lambda: fake_db

    client = TestClient(app)
    try:
        r = client.post(
            "/tree/members",
            json={"first_name": "Fut", "last_name": "Ure", "dob": "12/31/2999"},
            headers={"Authorization": "Bearer x"},
        )
        assert r.status_code == 400
        assert "future" in (r.json().get("detail") or "").lower()
    finally:
        routes_tree.get_db = orig_get_db
        app.dependency_overrides.clear()


def test_update_member_rejects_future_dob():
    from app import routes_tree
    from app.deps import get_current_username

    fake_db = FakeDB()

    app.dependency_overrides[get_current_username] = lambda: "tester"
    orig_get_db = routes_tree.get_db
    routes_tree.get_db = lambda: fake_db

    client = TestClient(app)
    try:
        r = client.post(
            "/tree/members",
            json={"first_name": "Ok", "last_name": "Past", "dob": "01/01/2000"},
            headers={"Authorization": "Bearer x"},
        )
        assert r.status_code == 200
        mid = r.json()["id"]
        r2 = client.patch(
            f"/tree/members/{mid}",
            json={"dob": "01/01/3000"},
            headers={"Authorization": "Bearer x"},
        )
        assert r2.status_code == 400
        assert "future" in (r2.json().get("detail") or "").lower()
    finally:
        routes_tree.get_db = orig_get_db
        app.dependency_overrides.clear()
