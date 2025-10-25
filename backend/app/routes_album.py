"""
Album routes for family space photo albums.
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from .album import delete_album_photo, upload_album_photo
from .config import settings
from .deps import get_current_username
from .firestore_client import get_db
from .models import AlbumPhoto, AlbumPhotoUpdate, AlbumStats, BulkPhotoUploadResponse
from .routes_spaces import get_user_space
from .utils.time import to_iso_string, utc_now

router = APIRouter(prefix="/spaces", tags=["album"])


def check_space_access(username: str, space_id: str) -> bool:
    """Check if user has access to the space."""
    user_space = get_user_space(username)
    return user_space == space_id


def is_photo_uploader(username: str, photo_id: str, space_id: str) -> bool:
    """Check if user is the photo uploader."""
    db = get_db()
    photo_ref = db.collection("album_photos").document(photo_id)
    photo_doc = photo_ref.get()

    if not photo_doc.exists:
        return False

    photo_data = photo_doc.to_dict()
    return photo_data.get("uploader_id") == username and photo_data.get("space_id") == space_id


@router.post("/{space_id}/album/photos", response_model=AlbumPhoto)
async def upload_photo(
    space_id: str,
    file: UploadFile = File(...),
    current_user: str = Depends(get_current_username),
):
    """Upload a photo to the album."""
    # Check space access
    if not check_space_access(current_user, space_id):
        raise HTTPException(status_code=403, detail="Access denied to this space")

    # Validate file type
    allowed_types = ["image/jpeg", "image/png", "image/webp", "image/gif"]
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400, detail=f"Invalid file type. Allowed: {', '.join(allowed_types)}"
        )

    # Read file content
    file_content = await file.read()
    file_size = len(file_content)

    # Check file size
    max_size = settings.album_max_upload_size_mb * 1024 * 1024
    if file_size > max_size:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Maximum size: {settings.album_max_upload_size_mb}MB",
        )

    # Upload to GCS
    upload_result = upload_album_photo(file_content, file.content_type, space_id)
    if not upload_result:
        raise HTTPException(status_code=500, detail="Failed to upload photo")

    photo_id, gcs_path, thumbnail_path, cdn_url, thumbnail_cdn_url, width, height = upload_result

    # Save to Firestore
    db = get_db()
    now = to_iso_string(utc_now())

    photo_data = {
        "space_id": space_id,
        "uploader_id": current_user,
        "filename": file.filename or "unknown",
        "gcs_path": gcs_path,
        "thumbnail_path": thumbnail_path,
        "cdn_url": cdn_url,
        "thumbnail_cdn_url": thumbnail_cdn_url,
        "upload_date": now,
        "file_size": file_size,
        "width": width,
        "height": height,
        "mime_type": file.content_type,
        "tags": [],
        "created_at": now,
        "updated_at": now,
    }

    photo_ref = db.collection("album_photos").document(photo_id)
    photo_ref.set(photo_data)

    return AlbumPhoto(id=photo_id, like_count=0, **photo_data)


@router.post("/{space_id}/album/photos/bulk", response_model=BulkPhotoUploadResponse)
async def bulk_upload_photos(
    space_id: str,
    files: List[UploadFile] = File(...),
    current_user: str = Depends(get_current_username),
):
    """Upload multiple photos to the album at once."""
    # Check space access
    if not check_space_access(current_user, space_id):
        raise HTTPException(status_code=403, detail="Access denied to this space")

    # Validate file count
    if len(files) > 50:
        raise HTTPException(
            status_code=400, detail="Too many files. Maximum 50 files per bulk upload"
        )

    if len(files) == 0:
        raise HTTPException(status_code=400, detail="No files provided")

    allowed_types = ["image/jpeg", "image/png", "image/webp", "image/gif"]
    max_size = settings.album_max_upload_size_mb * 1024 * 1024
    db = get_db()
    now = to_iso_string(utc_now())

    successful_uploads = []
    failed_uploads = []

    for file in files:
        try:
            # Validate file type
            if file.content_type not in allowed_types:
                failed_uploads.append(
                    {
                        "filename": file.filename or "unknown",
                        "error": f"Invalid file type: {file.content_type}",
                    }
                )
                continue

            # Read file content
            file_content = await file.read()
            file_size = len(file_content)

            # Check file size
            if file_size > max_size:
                failed_uploads.append(
                    {
                        "filename": file.filename or "unknown",
                        "error": f"File too large ({file_size} bytes). Max: {max_size} bytes",
                    }
                )
                continue

            # Upload to GCS
            upload_result = upload_album_photo(file_content, file.content_type, space_id)
            if not upload_result:
                failed_uploads.append(
                    {"filename": file.filename or "unknown", "error": "GCS upload failed"}
                )
                continue

            (
                photo_id,
                gcs_path,
                thumbnail_path,
                cdn_url,
                thumbnail_cdn_url,
                width,
                height,
            ) = upload_result

            # Save to Firestore
            photo_data = {
                "space_id": space_id,
                "uploader_id": current_user,
                "filename": file.filename or "unknown",
                "gcs_path": gcs_path,
                "thumbnail_path": thumbnail_path,
                "cdn_url": cdn_url,
                "thumbnail_cdn_url": thumbnail_cdn_url,
                "upload_date": now,
                "file_size": file_size,
                "width": width,
                "height": height,
                "mime_type": file.content_type,
                "tags": [],
                "created_at": now,
                "updated_at": now,
            }

            photo_ref = db.collection("album_photos").document(photo_id)
            photo_ref.set(photo_data)

            successful_uploads.append(AlbumPhoto(id=photo_id, like_count=0, **photo_data))

        except Exception as e:
            failed_uploads.append({"filename": file.filename or "unknown", "error": str(e)})

    return BulkPhotoUploadResponse(
        total=len(files),
        successful=len(successful_uploads),
        failed=len(failed_uploads),
        photos=successful_uploads,
        errors=failed_uploads,
    )


@router.get("/{space_id}/album/photos", response_model=List[AlbumPhoto])
def list_photos(
    space_id: str,
    current_user: str = Depends(get_current_username),
    uploader: Optional[str] = None,
    tags: Optional[str] = None,  # Comma-separated tags
    sort_by: str = "upload_date",
    sort_order: str = "desc",
    limit: int = 50,
):
    """List photos in the album with filtering and sorting."""
    # Check space access
    if not check_space_access(current_user, space_id):
        raise HTTPException(status_code=403, detail="Access denied to this space")

    db = get_db()
    query = db.collection("album_photos").where("space_id", "==", space_id)

    # Apply filters
    if uploader:
        query = query.where("uploader_id", "==", uploader)

    # Fetch all results for client-side filtering and sorting
    photos = []
    for doc in query.stream():
        photo_data = doc.to_dict()

        # Filter by tags if specified
        if tags:
            tag_list = [t.strip() for t in tags.split(",")]
            photo_tags = photo_data.get("tags", [])
            if not any(tag in photo_tags for tag in tag_list):
                continue

        # Count likes
        likes_query = db.collection("album_likes").where("photo_id", "==", doc.id)
        like_count = len(list(likes_query.stream()))

        photos.append(
            AlbumPhoto(
                id=doc.id,
                like_count=like_count,
                space_id=photo_data.get("space_id", ""),
                uploader_id=photo_data.get("uploader_id", ""),
                filename=photo_data.get("filename", ""),
                gcs_path=photo_data.get("gcs_path", ""),
                thumbnail_path=photo_data.get("thumbnail_path", ""),
                cdn_url=photo_data.get("cdn_url", ""),
                thumbnail_cdn_url=photo_data.get("thumbnail_cdn_url", ""),
                upload_date=photo_data.get("upload_date", ""),
                file_size=photo_data.get("file_size", 0),
                width=photo_data.get("width", 0),
                height=photo_data.get("height", 0),
                mime_type=photo_data.get("mime_type", ""),
                tags=photo_data.get("tags", []),
                created_at=photo_data.get("created_at", ""),
                updated_at=photo_data.get("updated_at", ""),
            )
        )

    # Sort photos
    reverse = sort_order == "desc"
    if sort_by == "upload_date":
        photos.sort(key=lambda p: p.upload_date, reverse=reverse)
    elif sort_by == "likes":
        photos.sort(key=lambda p: p.like_count, reverse=reverse)
    elif sort_by == "filename":
        photos.sort(key=lambda p: p.filename.lower(), reverse=reverse)
    elif sort_by == "uploader":
        photos.sort(key=lambda p: p.uploader_id, reverse=reverse)
    elif sort_by == "random":
        import random

        random.shuffle(photos)

    # Apply limit
    return photos[:limit]


@router.get("/{space_id}/album/photos/{photo_id}", response_model=AlbumPhoto)
def get_photo(
    space_id: str,
    photo_id: str,
    current_user: str = Depends(get_current_username),
):
    """Get a specific photo."""
    # Check space access
    if not check_space_access(current_user, space_id):
        raise HTTPException(status_code=403, detail="Access denied to this space")

    db = get_db()
    photo_ref = db.collection("album_photos").document(photo_id)
    photo_doc = photo_ref.get()

    if not photo_doc.exists:
        raise HTTPException(status_code=404, detail="Photo not found")

    photo_data = photo_doc.to_dict()

    # Verify photo belongs to this space
    if photo_data.get("space_id") != space_id:
        raise HTTPException(status_code=404, detail="Photo not found")

    # Count likes
    likes_query = db.collection("album_likes").where("photo_id", "==", photo_id)
    like_count = len(list(likes_query.stream()))

    return AlbumPhoto(id=photo_id, like_count=like_count, **photo_data)


@router.delete("/{space_id}/album/photos/{photo_id}")
def delete_photo(
    space_id: str,
    photo_id: str,
    current_user: str = Depends(get_current_username),
):
    """Delete a photo (uploader or admin only)."""
    # Check space access
    if not check_space_access(current_user, space_id):
        raise HTTPException(status_code=403, detail="Access denied to this space")

    # Check if user is uploader (admin check would go here too)
    if not is_photo_uploader(current_user, photo_id, space_id):
        raise HTTPException(status_code=403, detail="Only the uploader can delete this photo")

    db = get_db()
    photo_ref = db.collection("album_photos").document(photo_id)
    photo_doc = photo_ref.get()

    if not photo_doc.exists:
        raise HTTPException(status_code=404, detail="Photo not found")

    photo_data = photo_doc.to_dict()

    # Delete from GCS
    delete_album_photo(photo_data.get("gcs_path", ""), photo_data.get("thumbnail_path", ""))

    # Delete likes
    likes_query = db.collection("album_likes").where("photo_id", "==", photo_id)
    for like_doc in likes_query.stream():
        like_doc.reference.delete()

    # Delete photo document
    photo_ref.delete()

    return {"message": "Photo deleted successfully"}


@router.post("/{space_id}/album/photos/{photo_id}/like")
def like_photo(
    space_id: str,
    photo_id: str,
    current_user: str = Depends(get_current_username),
):
    """Like a photo."""
    # Check space access
    if not check_space_access(current_user, space_id):
        raise HTTPException(status_code=403, detail="Access denied to this space")

    # Verify photo exists and belongs to space
    db = get_db()
    photo_ref = db.collection("album_photos").document(photo_id)
    photo_doc = photo_ref.get()

    if not photo_doc.exists:
        raise HTTPException(status_code=404, detail="Photo not found")

    photo_data = photo_doc.to_dict()
    if photo_data.get("space_id") != space_id:
        raise HTTPException(status_code=404, detail="Photo not found")

    # Check if already liked
    likes_query = (
        db.collection("album_likes")
        .where("photo_id", "==", photo_id)
        .where("user_id", "==", current_user)
    )
    existing_likes = list(likes_query.stream())

    if existing_likes:
        raise HTTPException(status_code=400, detail="Already liked")

    # Create like
    now = to_iso_string(utc_now())
    like_data = {
        "photo_id": photo_id,
        "user_id": current_user,
        "space_id": space_id,
        "created_at": now,
    }

    like_ref = db.collection("album_likes").document()
    like_ref.set(like_data)

    return {"message": "Photo liked", "like_id": like_ref.id}


@router.delete("/{space_id}/album/photos/{photo_id}/like")
def unlike_photo(
    space_id: str,
    photo_id: str,
    current_user: str = Depends(get_current_username),
):
    """Unlike a photo."""
    # Check space access
    if not check_space_access(current_user, space_id):
        raise HTTPException(status_code=403, detail="Access denied to this space")

    db = get_db()

    # Find the like
    likes_query = (
        db.collection("album_likes")
        .where("photo_id", "==", photo_id)
        .where("user_id", "==", current_user)
    )
    likes = list(likes_query.stream())

    if not likes:
        raise HTTPException(status_code=404, detail="Like not found")

    # Delete the like
    for like_doc in likes:
        like_doc.reference.delete()

    return {"message": "Photo unliked"}


@router.put("/{space_id}/album/photos/{photo_id}/tags", response_model=AlbumPhoto)
def update_tags(
    space_id: str,
    photo_id: str,
    tag_update: AlbumPhotoUpdate,
    current_user: str = Depends(get_current_username),
):
    """Update photo tags."""
    # Check space access
    if not check_space_access(current_user, space_id):
        raise HTTPException(status_code=403, detail="Access denied to this space")

    db = get_db()
    photo_ref = db.collection("album_photos").document(photo_id)
    photo_doc = photo_ref.get()

    if not photo_doc.exists:
        raise HTTPException(status_code=404, detail="Photo not found")

    photo_data = photo_doc.to_dict()

    # Verify photo belongs to this space
    if photo_data.get("space_id") != space_id:
        raise HTTPException(status_code=404, detail="Photo not found")

    # Update tags
    now = to_iso_string(utc_now())
    photo_ref.update({"tags": tag_update.tags, "updated_at": now})

    photo_data["tags"] = tag_update.tags
    photo_data["updated_at"] = now

    # Count likes
    likes_query = db.collection("album_likes").where("photo_id", "==", photo_id)
    like_count = len(list(likes_query.stream()))

    return AlbumPhoto(id=photo_id, like_count=like_count, **photo_data)


@router.get("/{space_id}/album/stats", response_model=AlbumStats)
def get_album_stats(
    space_id: str,
    current_user: str = Depends(get_current_username),
):
    """Get album statistics."""
    # Check space access
    if not check_space_access(current_user, space_id):
        raise HTTPException(status_code=403, detail="Access denied to this space")

    db = get_db()

    # Count total photos
    photos_query = db.collection("album_photos").where("space_id", "==", space_id)
    photos = list(photos_query.stream())
    total_photos = len(photos)

    # Count unique uploaders
    uploaders = set()
    recent_uploads = 0
    from datetime import datetime, timedelta

    seven_days_ago = utc_now() - timedelta(days=7)

    for photo_doc in photos:
        photo_data = photo_doc.to_dict()
        uploaders.add(photo_data.get("uploader_id", ""))

        # Count recent uploads
        upload_date_str = photo_data.get("upload_date", "")
        try:
            upload_date = datetime.fromisoformat(upload_date_str.replace("Z", "+00:00"))
            if upload_date > seven_days_ago:
                recent_uploads += 1
        except (ValueError, AttributeError):
            pass

    total_uploaders = len(uploaders)

    # Count total likes for this space
    likes_query = db.collection("album_likes").where("space_id", "==", space_id)
    total_likes = len(list(likes_query.stream()))

    return AlbumStats(
        total_photos=total_photos,
        total_likes=total_likes,
        total_uploaders=total_uploaders,
        recent_uploads=recent_uploads,
    )
