from app.firestore_client import get_db


class DummyClient:
    def __init__(self, *args, **kwargs):
        pass

    def collection(self, name):
        class C:
            def document(self, *args, **kwargs):
                return object()

        return C()


def test_firestore_client(monkeypatch):
    """Test firestore client returns a client"""
    # Avoid ADC lookups by stubbing the Firestore client
    import app.firestore_client as fc

    monkeypatch.setattr(fc.firestore, "Client", DummyClient)
    db = get_db()
    # Should return some kind of client object
    assert db is not None
    # Should have collection method
    assert hasattr(db, "collection")
