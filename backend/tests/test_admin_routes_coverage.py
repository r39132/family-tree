"""Tests for app/routes_admin.py to increase coverage."""

from unittest.mock import Mock, patch

import pytest
from fastapi import HTTPException

from app.routes_admin import log_admin_action, require_admin


def test_require_admin_user_not_found():
    """Test require_admin when user document doesn't exist."""
    with patch("app.routes_admin.get_db") as mock_get_db:
        mock_db = Mock()
        mock_get_db.return_value = mock_db

        # Mock user document that doesn't exist
        mock_doc = Mock()
        mock_doc.exists = False
        mock_db.collection.return_value.document.return_value.get.return_value = mock_doc

        with pytest.raises(HTTPException) as exc_info:
            require_admin("test_user")

        assert exc_info.value.status_code == 404
        assert exc_info.value.detail == "User not found"


def test_require_admin_not_admin():
    """Test require_admin when user is not an admin."""
    with patch("app.routes_admin.get_db") as mock_get_db:
        mock_db = Mock()
        mock_get_db.return_value = mock_db

        # Mock user document that exists but is not admin
        mock_doc = Mock()
        mock_doc.exists = True
        mock_doc.to_dict.return_value = {"roles": ["user"]}
        mock_db.collection.return_value.document.return_value.get.return_value = mock_doc

        with pytest.raises(HTTPException) as exc_info:
            require_admin("test_user")

        assert exc_info.value.status_code == 403
        assert exc_info.value.detail == "Admin access required"


def test_require_admin_no_roles():
    """Test require_admin when user has no roles."""
    with patch("app.routes_admin.get_db") as mock_get_db:
        mock_db = Mock()
        mock_get_db.return_value = mock_db

        # Mock user document with no roles
        mock_doc = Mock()
        mock_doc.exists = True
        mock_doc.to_dict.return_value = {}
        mock_db.collection.return_value.document.return_value.get.return_value = mock_doc

        with pytest.raises(HTTPException) as exc_info:
            require_admin("test_user")

        assert exc_info.value.status_code == 403
        assert exc_info.value.detail == "Admin access required"


def test_require_admin_null_roles():
    """Test require_admin when user has null roles."""
    with patch("app.routes_admin.get_db") as mock_get_db:
        mock_db = Mock()
        mock_get_db.return_value = mock_db

        # Mock user document with null roles
        mock_doc = Mock()
        mock_doc.exists = True
        mock_doc.to_dict.return_value = {"roles": None}
        mock_db.collection.return_value.document.return_value.get.return_value = mock_doc

        with pytest.raises(HTTPException) as exc_info:
            require_admin("test_user")

        assert exc_info.value.status_code == 403
        assert exc_info.value.detail == "Admin access required"


def test_require_admin_success():
    """Test require_admin when user is admin."""
    with patch("app.routes_admin.get_db") as mock_get_db:
        mock_db = Mock()
        mock_get_db.return_value = mock_db

        # Mock user document that is admin
        mock_doc = Mock()
        mock_doc.exists = True
        mock_doc.to_dict.return_value = {"roles": ["admin", "user"]}
        mock_db.collection.return_value.document.return_value.get.return_value = mock_doc

        result = require_admin("admin_user")
        assert result == "admin_user"


def test_log_admin_action_basic():
    """Test log_admin_action with basic parameters."""
    with patch("app.routes_admin.get_db") as mock_get_db:
        mock_db = Mock()
        mock_get_db.return_value = mock_db
        mock_collection = Mock()
        mock_db.collection.return_value = mock_collection

        log_admin_action("admin1", "evict", "user1")

        # Verify the collection was called correctly
        mock_db.collection.assert_called_once_with("admin_logs")
        mock_collection.add.assert_called_once()

        # Check the payload structure
        call_args = mock_collection.add.call_args[0][0]
        assert call_args["actor"] == "admin1"
        assert call_args["action"] == "evict"
        assert call_args["target"] == "user1"
        assert "timestamp" in call_args


def test_log_admin_action_with_extra():
    """Test log_admin_action with extra parameters."""
    with patch("app.routes_admin.get_db") as mock_get_db:
        mock_db = Mock()
        mock_get_db.return_value = mock_db
        mock_collection = Mock()
        mock_db.collection.return_value = mock_collection

        extra_data = {"evicted_at": 1234567890, "reason": "violation"}
        log_admin_action("admin1", "evict", "user1", extra_data)

        # Check the payload includes extra data
        call_args = mock_collection.add.call_args[0][0]
        assert call_args["actor"] == "admin1"
        assert call_args["action"] == "evict"
        assert call_args["target"] == "user1"
        assert call_args["extra_evicted_at"] == 1234567890
        assert call_args["extra_reason"] == "violation"
        assert "timestamp" in call_args
