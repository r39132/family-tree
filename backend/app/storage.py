"""
Google Cloud Storage utilities for profile picture uploads.
"""

import io
import uuid
from datetime import timedelta
from typing import Optional

from google.cloud import storage
from PIL import Image

from app.config import settings


def get_storage_client() -> Optional[storage.Client]:
    """Get Google Cloud Storage client if bucket is configured."""
    if not settings.gcs_bucket_name:
        return None
    return storage.Client()


def upload_profile_picture(
    file_content: bytes, content_type: str, member_id: str, space_id: str = "demo"
) -> Optional[str]:
    """
    Upload a profile picture to Google Cloud Storage.

    Args:
        file_content: The image file content as bytes
        content_type: The MIME type of the image
        member_id: The ID of the member this picture belongs to
        space_id: The family space ID (for organizing storage by space)

    Returns:
        A signed URL for the uploaded image (valid for 7 days), or None if upload failed
    """
    client = get_storage_client()
    if not client:
        return None

    # Validate and optimize the image
    try:
        image = Image.open(io.BytesIO(file_content))

        # Convert to RGB if necessary (handles PNG with transparency)
        if image.mode in ("RGBA", "LA", "P"):
            background = Image.new("RGB", image.size, (255, 255, 255))
            if image.mode == "P":
                image = image.convert("RGBA")
            background.paste(image, mask=image.split()[-1] if image.mode == "RGBA" else None)
            image = background

        # Resize if too large (max 800x800 for profile pictures)
        max_size = (800, 800)
        if image.size[0] > max_size[0] or image.size[1] > max_size[1]:
            image.thumbnail(max_size, Image.Resampling.LANCZOS)

        # Save optimized image to bytes
        output = io.BytesIO()
        image.save(output, format="JPEG", quality=85, optimize=True)
        optimized_content = output.getvalue()

    except Exception as e:
        print(f"Error processing image: {e}")
        return None

    # Generate a unique filename organized by space
    file_extension = "jpg"  # Always save as JPEG after optimization
    filename = f"{space_id}/profile-pictures/{member_id}/{uuid.uuid4()}.{file_extension}"

    try:
        bucket = client.bucket(settings.gcs_bucket_name)
        blob = bucket.blob(filename)

        # Upload with appropriate content type
        blob.upload_from_string(optimized_content, content_type="image/jpeg")

        # Generate a signed URL (valid for 7 days) for secure access without public bucket
        signed_url = blob.generate_signed_url(
            version="v4",
            expiration=timedelta(days=7),
            method="GET",
        )

        return signed_url

    except Exception as e:
        print(f"Error uploading to GCS: {e}")
        return None


def delete_profile_picture(picture_url: str) -> bool:
    """
    Delete a profile picture from Google Cloud Storage.

    Args:
        picture_url: The signed URL or path of the image to delete

    Returns:
        True if deletion was successful, False otherwise
    """
    client = get_storage_client()
    if not client or not picture_url:
        return False

    try:
        # Extract blob name from URL
        # Format: https://storage.googleapis.com/bucket-name/path/to/file or signed URL
        if settings.gcs_bucket_name not in picture_url:
            return False

        # For signed URLs, extract the path before the query parameters
        url_path = picture_url.split("?")[0]
        blob_name = url_path.split(f"{settings.gcs_bucket_name}/")[-1]
        bucket = client.bucket(settings.gcs_bucket_name)
        blob = bucket.blob(blob_name)
        blob.delete()
        return True

    except Exception as e:
        print(f"Error deleting from GCS: {e}")
        return False
