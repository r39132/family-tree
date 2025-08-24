from app.firestore_client import get_db


def test_firestore_client():
    """Test firestore client returns a client"""
    db = get_db()
    # Should return some kind of client object
    assert db is not None
    # Should have collection method
    assert hasattr(db, 'collection')
