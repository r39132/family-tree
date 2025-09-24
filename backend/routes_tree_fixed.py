"""
Fixed tree routes with proper space isolation and atomic operations.
This replaces the buggy routes_tree.py with properly implemented functions.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from deps import get_current_user
from fastapi import APIRouter, Depends, HTTPException
from firestore_client import get_db
from google.cloud import firestore
from pydantic import BaseModel

router = APIRouter()
logger = logging.getLogger(__name__)


class TreeVersionResponse(BaseModel):
    id: str
    version: int
    created_at: str
    message: str


class RecoverRequest(BaseModel):
    version_id: str


class UnsavedResponse(BaseModel):
    unsaved: bool
    current_relations_count: int
    saved_relations_count: int


class TreeVersionsResponse(BaseModel):
    versions: List[Dict[str, Any]]
    active_version: Optional[str]


def _get_user_space(username: str, db) -> str:
    """Get the current space for a user"""
    user_doc = db.collection("users").document(username).get()
    if not user_doc.exists:
        raise HTTPException(status_code=404, detail="User not found")

    user_data = user_doc.to_dict()
    space_id = user_data.get("current_space")

    if not space_id:
        raise HTTPException(status_code=400, detail="User has no active space")

    return space_id


def _validate_space_access(username: str, space_id: str, db) -> bool:
    """Validate that user has access to the specified space"""
    user_space = _get_user_space(username, db)
    return user_space == space_id


def _snapshot_relations(space_id: str, db) -> List[Dict[str, Any]]:
    """Create a snapshot of current relations for a space"""
    relations_query = db.collection("relations").where("space_id", "==", space_id)

    relations = []
    for doc in relations_query.stream():
        relation_data = doc.to_dict()
        # Ensure space_id is included in snapshot
        relation_data["space_id"] = space_id
        relations.append(relation_data)

    return relations


def _get_space_active_version(space_id: str, db) -> Optional[str]:
    """Get the active version for a specific space"""
    # Use space-specific active version tracking
    state_doc = db.collection("tree_state").document(f"active_version_{space_id}").get()

    if state_doc.exists:
        return state_doc.to_dict().get("version_id")

    return None


def _set_space_active_version(space_id: str, version_id: str, db) -> None:
    """Set the active version for a specific space"""
    db.collection("tree_state").document(f"active_version_{space_id}").set(
        {
            "version_id": version_id,
            "space_id": space_id,
            "updated_at": datetime.utcnow().isoformat(),
        }
    )


def _get_latest_version_number(space_id: str, db) -> int:
    """Get the next version number for a space"""
    versions_query = (
        db.collection("tree_versions")
        .where("space_id", "==", space_id)
        .order_by("version", direction=firestore.Query.DESCENDING)
        .limit(1)
    )

    latest = list(versions_query.stream())
    if latest:
        return latest[0].to_dict().get("version", 0) + 1

    return 1


@router.post("/save", response_model=TreeVersionResponse)
def save_tree(current_user: dict = Depends(get_current_user)):
    """Save current tree state as a new version with proper space isolation"""
    db = get_db()
    username = current_user.get("username")

    try:
        # Get user's space
        space_id = _get_user_space(username, db)

        # Create snapshot of current relations
        relations = _snapshot_relations(space_id, db)

        if not relations:
            raise HTTPException(status_code=400, detail="No relations found to save")

        # Get next version number for this space
        version_number = _get_latest_version_number(space_id, db)

        # Create version document
        version_data = {
            "space_id": space_id,
            "version": version_number,
            "relations": relations,
            "created_at": datetime.utcnow().isoformat(),
            "created_by": username,
            "relations_count": len(relations),
        }

        # Save version atomically
        version_ref = db.collection("tree_versions").document()
        version_ref.set(version_data)

        # Update space-specific active version
        _set_space_active_version(space_id, version_ref.id, db)

        logger.info(f"Saved tree version {version_number} for space {space_id} by user {username}")

        return TreeVersionResponse(
            id=version_ref.id,
            version=version_number,
            created_at=version_data["created_at"],
            message=f"Tree saved successfully as version {version_number}",
        )

    except Exception as e:
        logger.error(f"Error saving tree for user {username}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to save tree: {str(e)}")


@router.post("/recover")
def recover_tree(request: RecoverRequest, current_user: dict = Depends(get_current_user)):
    """Recover tree to a specific version with atomic operations and space validation"""
    db = get_db()
    username = current_user.get("username")

    try:
        # Get user's space
        space_id = _get_user_space(username, db)

        # Get the version to recover
        version_doc = db.collection("tree_versions").document(request.version_id).get()

        if not version_doc.exists:
            raise HTTPException(status_code=404, detail="Version not found")

        version_data = version_doc.to_dict()

        # SECURITY: Validate space access
        version_space_id = version_data.get("space_id")
        if not version_space_id or version_space_id != space_id:
            raise HTTPException(
                status_code=403, detail="Access denied: Version belongs to different space"
            )

        # Get relations from version
        saved_relations = version_data.get("relations", [])

        # ATOMIC OPERATION: Use Firestore batch for recovery
        batch = db.batch()

        # Step 1: Delete all current relations for this space
        current_relations_query = db.collection("relations").where("space_id", "==", space_id)

        relations_to_delete = []
        for doc in current_relations_query.stream():
            relations_to_delete.append(doc.reference)

        # Add deletions to batch
        for relation_ref in relations_to_delete:
            batch.delete(relation_ref)

        # Step 2: Add recovered relations to batch
        for relation_data in saved_relations:
            # Ensure space_id consistency
            relation_data["space_id"] = space_id
            new_relation_ref = db.collection("relations").document()
            batch.set(new_relation_ref, relation_data)

        # Step 3: Update active version for this space
        active_version_ref = db.collection("tree_state").document(f"active_version_{space_id}")
        batch.set(
            active_version_ref,
            {
                "version_id": request.version_id,
                "space_id": space_id,
                "recovered_at": datetime.utcnow().isoformat(),
                "recovered_by": username,
            },
        )

        # Commit the entire batch atomically
        batch.commit()

        logger.info(
            f"Recovered tree to version {request.version_id} for space {space_id} by user {username}"
        )

        return {
            "message": f"Successfully recovered to version {version_data.get('version', 'unknown')}",
            "version_id": request.version_id,
            "relations_restored": len(saved_relations),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error recovering tree for user {username}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to recover tree: {str(e)}")


@router.get("/versions", response_model=TreeVersionsResponse)
def list_versions(current_user: dict = Depends(get_current_user)):
    """List tree versions for user's space only"""
    db = get_db()
    username = current_user.get("username")

    try:
        # Get user's space
        space_id = _get_user_space(username, db)

        # Get versions for this space only
        versions_query = (
            db.collection("tree_versions")
            .where("space_id", "==", space_id)
            .order_by("version", direction=firestore.Query.DESCENDING)
        )

        versions = []
        for doc in versions_query.stream():
            version_data = doc.to_dict()
            versions.append(
                {
                    "id": doc.id,
                    "version": version_data.get("version"),
                    "created_at": version_data.get("created_at"),
                    "created_by": version_data.get("created_by"),
                    "relations_count": version_data.get(
                        "relations_count", len(version_data.get("relations", []))
                    ),
                }
            )

        # Get space-specific active version
        active_version = _get_space_active_version(space_id, db)

        return TreeVersionsResponse(versions=versions, active_version=active_version)

    except Exception as e:
        logger.error(f"Error listing versions for user {username}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to list versions: {str(e)}")


@router.get("/unsaved", response_model=UnsavedResponse)
def unsaved_changes(current_user: dict = Depends(get_current_user)):
    """Check for unsaved changes with proper space context"""
    db = get_db()
    username = current_user.get("username")

    try:
        # Get user's space
        space_id = _get_user_space(username, db)

        # Get current relations count for this space
        current_relations_query = db.collection("relations").where("space_id", "==", space_id)
        current_relations = list(current_relations_query.stream())
        current_count = len(current_relations)

        # Get active version for this space
        active_version_id = _get_space_active_version(space_id, db)

        saved_count = 0
        if active_version_id:
            version_doc = db.collection("tree_versions").document(active_version_id).get()
            if version_doc.exists:
                version_data = version_doc.to_dict()
                # Validate space consistency
                if version_data.get("space_id") == space_id:
                    saved_relations = version_data.get("relations", [])
                    saved_count = len(saved_relations)

        unsaved = current_count != saved_count

        return UnsavedResponse(
            unsaved=unsaved,
            current_relations_count=current_count,
            saved_relations_count=saved_count,
        )

    except Exception as e:
        logger.error(f"Error checking unsaved changes for user {username}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to check unsaved changes: {str(e)}")
