"""
Google Cloud Storage utilities for album photo uploads.
"""

import io
import uuid
from datetime import timedelta
from typing import Optional, Tuple

from google.cloud import storage
from PIL import Image

from app.config import settings


def get_album_storage_client() -> Optional[storage.Client]:
    """Get Google Cloud Storage client if album bucket is configured."""
    if not settings.album_bucket_name:
        return None
    return storage.Client()


def extract_gps_coordinates(image: Image.Image) -> Tuple[Optional[float], Optional[float]]:
    """
    Extract GPS coordinates from image EXIF data.

    Args:
        image: PIL Image object

    Returns:
        Tuple of (latitude, longitude) or (None, None) if not available
    """
    try:
        exif = image.getexif()
        if not exif:
            return None, None

        # EXIF tags for GPS info
        gps_info = exif.get(34853)  # GPSInfo tag
        if not gps_info:
            return None, None

        # Helper function to convert GPS coordinates
        def get_decimal_from_dms(dms, ref):
            """Convert degrees, minutes, seconds to decimal degrees."""
            degrees = float(dms[0])
            minutes = float(dms[1]) / 60.0
            seconds = float(dms[2]) / 3600.0
            decimal = degrees + minutes + seconds
            
            if ref in ['S', 'W']:
                decimal = -decimal
            
            return decimal

        lat = None
        lon = None

        # Extract latitude
        if 2 in gps_info and 1 in gps_info:  # GPSLatitude and GPSLatitudeRef
            lat = get_decimal_from_dms(gps_info[2], gps_info[1])

        # Extract longitude
        if 4 in gps_info and 3 in gps_info:  # GPSLongitude and GPSLongitudeRef
            lon = get_decimal_from_dms(gps_info[4], gps_info[3])

        return lat, lon

    except Exception as e:
        print(f"Error extracting GPS coordinates: {e}")
        return None, None


def generate_thumbnail(image: Image.Image, size: int = 300) -> bytes:
    """
    Generate a thumbnail from an image.

    Args:
        image: PIL Image object
        size: Thumbnail size (will be size x size)

    Returns:
        Thumbnail image as bytes
    """
    # Convert to RGB if necessary
    if image.mode in ("RGBA", "LA", "P"):
        background = Image.new("RGB", image.size, (255, 255, 255))
        if image.mode == "P":
            image = image.convert("RGBA")
        if image.mode in ("RGBA", "LA"):
            background.paste(image, mask=image.split()[-1])
        image = background

    # Create thumbnail
    image.thumbnail((size, size), Image.Resampling.LANCZOS)

    # Save to bytes
    output = io.BytesIO()
    image.save(output, format="JPEG", quality=85, optimize=True)
    return output.getvalue()


def upload_album_photo(
    file_content: bytes, content_type: str, space_id: str
) -> Optional[Tuple[str, str, str, str, str, int, int, Optional[float], Optional[float]]]:
    """
    Upload an album photo to Google Cloud Storage.

    Args:
        file_content: The image file content as bytes
        content_type: The MIME type of the image
        space_id: The family space ID

    Returns:
        Tuple of (photo_id, gcs_path, thumbnail_path, cdn_url, thumbnail_cdn_url, width, height, gps_latitude, gps_longitude)
        or None if upload failed
    """
    client = get_album_storage_client()
    if not client:
        return None

    # Validate and process the image
    try:
        image = Image.open(io.BytesIO(file_content))
        width, height = image.size

        # Extract GPS coordinates
        gps_latitude, gps_longitude = extract_gps_coordinates(image)

        # Optimize if too large (>2MB)
        if len(file_content) > 2 * 1024 * 1024:
            output = io.BytesIO()
            image.save(output, format="JPEG", quality=85, optimize=True)
            file_content = output.getvalue()

        # Generate thumbnail
        thumbnail_content = generate_thumbnail(image.copy(), settings.album_thumbnail_size)

    except Exception as e:
        print(f"Error processing image: {e}")
        return None

    # Generate unique photo ID
    photo_id = str(uuid.uuid4())
    file_extension = "jpg"

    # Define paths
    original_path = f"{space_id}/originals/{photo_id}.{file_extension}"
    thumbnail_path = f"{space_id}/thumbnails/{photo_id}_thumb.jpg"

    try:
        bucket = client.bucket(settings.album_bucket_name)

        # Upload original
        original_blob = bucket.blob(original_path)
        original_blob.upload_from_string(file_content, content_type="image/jpeg")

        # Upload thumbnail
        thumbnail_blob = bucket.blob(thumbnail_path)
        thumbnail_blob.upload_from_string(thumbnail_content, content_type="image/jpeg")

        # Generate CDN URLs or signed URLs
        if settings.cdn_base_url:
            cdn_url = f"{settings.cdn_base_url}/{settings.album_bucket_name}/{original_path}"
            thumbnail_cdn_url = (
                f"{settings.cdn_base_url}/{settings.album_bucket_name}/{thumbnail_path}"
            )
        else:
            # Fallback to signed URLs
            cdn_url = original_blob.generate_signed_url(
                version="v4",
                expiration=timedelta(days=settings.signed_url_expiration_days),
                method="GET",
            )
            thumbnail_cdn_url = thumbnail_blob.generate_signed_url(
                version="v4",
                expiration=timedelta(days=settings.signed_url_expiration_days),
                method="GET",
            )

        return (photo_id, original_path, thumbnail_path, cdn_url, thumbnail_cdn_url, width, height, gps_latitude, gps_longitude)

    except Exception as e:
        print(f"Error uploading to GCS: {e}")
        return None


def delete_album_photo(gcs_path: str, thumbnail_path: str) -> bool:
    """
    Delete an album photo and its thumbnail from Google Cloud Storage.

    Args:
        gcs_path: The GCS path of the original photo
        thumbnail_path: The GCS path of the thumbnail

    Returns:
        True if deletion was successful, False otherwise
    """
    client = get_album_storage_client()
    if not client:
        return False

    try:
        bucket = client.bucket(settings.album_bucket_name)

        # Delete original
        original_blob = bucket.blob(gcs_path)
        original_blob.delete()

        # Delete thumbnail
        thumbnail_blob = bucket.blob(thumbnail_path)
        thumbnail_blob.delete()

        return True

    except Exception as e:
        print(f"Error deleting from GCS: {e}")
        return False


def get_cdn_url(gcs_path: str) -> Optional[str]:
    """
    Generate a CDN URL for a photo.

    Args:
        gcs_path: The GCS path of the photo

    Returns:
        CDN URL or signed URL
    """
    if settings.cdn_base_url:
        return f"{settings.cdn_base_url}/{settings.album_bucket_name}/{gcs_path}"

    client = get_album_storage_client()
    if not client:
        return None

    try:
        bucket = client.bucket(settings.album_bucket_name)
        blob = bucket.blob(gcs_path)

        signed_url = blob.generate_signed_url(
            version="v4",
            expiration=timedelta(days=settings.signed_url_expiration_days),
            method="GET",
        )

        return signed_url

    except Exception as e:
        print(f"Error generating signed URL: {e}")
        return None
