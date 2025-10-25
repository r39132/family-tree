import smtplib
import types
from typing import Dict

import pytest


class FakeCollection:
    def __init__(self, name, db):
        self.name = name
        self.db = db
        self.docs: Dict[str, dict] = {}
        self._auto = 0

    # Document reference
    def document(self, doc_id=None):
        if doc_id is None:
            doc_id = f"{self.name}-{self._auto}"
            self._auto += 1
        coll = self

        class Doc:
            def __init__(self, id):
                self.id = id

            def get(self):
                data = coll.docs.get(self.id)
                return types.SimpleNamespace(exists=data is not None, to_dict=lambda: data)

            def set(self, data):
                coll.docs[self.id] = dict(data)

            def update(self, data):
                coll.docs[self.id] = {**(coll.docs.get(self.id) or {}), **data}

            def delete(self):
                coll.docs.pop(self.id, None)

        return Doc(doc_id)

    def add(self, data):
        doc = self.document()
        doc.set(data)
        return doc

    # Query API (subset)
    class Query:
        def __init__(self, coll, where=None, order_by=None, direction="ASCENDING", limit=None):
            self.coll = coll
            self._where = where  # tuple(field, op, value)
            self._order_by = order_by
            self._direction = direction
            self._limit = limit

        def where(self, field_path=None, op_string=None, value=None, *, filter=None):
            cond = None
            if filter is not None:
                # Using the filter keyword argument with fake FF class
                if hasattr(filter, "field_path"):
                    # Real FieldFilter
                    cond = (filter.field_path, filter.op_string, filter.value)
                else:
                    # Fake FF class used in tests
                    cond = (filter.field, filter.op, filter.value)
            elif field_path is not None and op_string is not None:
                # Using positional arguments
                cond = (field_path, op_string, value)
            return FakeCollection.Query(
                self.coll, cond, self._order_by, self._direction, self._limit
            )

        def order_by(self, field, direction="ASCENDING"):
            return FakeCollection.Query(self.coll, self._where, field, direction, self._limit)

        def limit(self, n):
            return FakeCollection.Query(self.coll, self._where, self._order_by, self._direction, n)

        def stream(self):
            items = list(self.coll.docs.items())
            # where filter
            if self._where:
                f, op, v = self._where
                if op == "==":
                    items = [(i, d) for i, d in items if d.get(f) == v]
            # ordering
            if self._order_by:
                reverse = self._direction == "DESCENDING"
                items.sort(key=lambda t: t[1].get(self._order_by), reverse=reverse)
            # limit
            if self._limit is not None:
                items = items[: self._limit]
            for id, data in items:
                yield types.SimpleNamespace(id=id, to_dict=lambda d=data: d)

    def where(self, field_path=None, op_string=None, value=None, *, filter=None):
        cond = None
        if filter is not None:
            # Using the filter keyword argument with fake FF class
            if hasattr(filter, "field_path"):
                # Real FieldFilter
                cond = (filter.field_path, filter.op_string, filter.value)
            else:
                # Fake FF class used in tests
                cond = (filter.field, filter.op, filter.value)
        elif field_path is not None and op_string is not None:
            # Using positional arguments
            cond = (field_path, op_string, value)
        return FakeCollection.Query(self, cond)

    def order_by(self, field, direction="ASCENDING"):
        return FakeCollection.Query(self, None, field, direction)

    def limit(self, n):
        return FakeCollection.Query(self, None, None, "ASCENDING", n)

    def stream(self):
        for id, data in self.docs.items():
            yield types.SimpleNamespace(id=id, to_dict=lambda d=data: d)


class FakeDB:
    def __init__(self):
        self.cols = {
            "members": FakeCollection("members", self),
            "relations": FakeCollection("relations", self),
            "member_keys": FakeCollection("member_keys", self),
            "tree_versions": FakeCollection("tree_versions", self),
            "tree_state": FakeCollection("tree_state", self),
            "users": FakeCollection("users", self),
            "family_spaces": FakeCollection("family_spaces", self),
            "album_photos": FakeCollection("album_photos", self),
            "album_likes": FakeCollection("album_likes", self),
        }

    def collection(self, name):
        return self.cols[name]


@pytest.fixture(autouse=True)
def fake_db(monkeypatch):
    # Replace Firestore client and FieldFilter with test doubles
    db = FakeDB()

    def _get_db():
        return db

    class FF:
        def __init__(self, field, op, value):
            self.field = field
            self.op = op
            self.value = value

    monkeypatch.setattr("app.firestore_client.get_db", _get_db)
    monkeypatch.setattr("app.routes_tree.FieldFilter", FF, raising=False)
    yield


@pytest.fixture(autouse=True)
def mock_smtp(monkeypatch):
    sent_messages = []

    class DummySMTP:
        def __init__(self, host, port, *args, **kwargs):
            self.host = host
            self.port = port

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def starttls(self):
            pass

        def login(self, user, password):
            pass

        def send_message(self, msg):
            sent_messages.append(msg)

    monkeypatch.setattr(smtplib, "SMTP", DummySMTP)
    return sent_messages
