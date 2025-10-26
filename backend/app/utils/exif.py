"""
EXIF metadata extraction utilities for photos.
"""

from datetime import datetime
from typing import Optional

from PIL import Image
from PIL.ExifTags import TAGS


def extract_exif_metadata(image: Image.Image) -> dict:
    """
    Extract EXIF metadata from an image.

    Args:
        image: PIL Image object

    Returns:
        Dictionary containing extracted EXIF metadata:
        - photo_date: ISO 8601 timestamp from DateTimeOriginal or None
        - camera_make: Camera manufacturer or None
        - camera_model: Camera model or None
        - gps_latitude: GPS latitude or None
        - gps_longitude: GPS longitude or None
    """
    metadata = {
        "photo_date": None,
        "camera_make": None,
        "camera_model": None,
        "gps_latitude": None,
        "gps_longitude": None,
    }

    try:
        exif = image.getexif()
        if not exif:
            return metadata

        for tag_id, value in exif.items():
            tag = TAGS.get(tag_id, tag_id)

            if tag == "DateTimeOriginal" and value:
                metadata["photo_date"] = _parse_exif_datetime(value)
            elif tag == "Make" and value:
                metadata["camera_make"] = str(value).strip()
            elif tag == "Model" and value:
                metadata["camera_model"] = str(value).strip()
            elif tag == "GPSInfo" and value:
                gps_data = _extract_gps_coordinates(value)
                if gps_data:
                    metadata["gps_latitude"] = gps_data.get("latitude")
                    metadata["gps_longitude"] = gps_data.get("longitude")

    except Exception as e:
        # Log but don't fail if EXIF extraction fails
        print(f"Warning: EXIF extraction failed: {e}")

    return metadata


def _parse_exif_datetime(exif_datetime: str) -> Optional[str]:
    """
    Parse EXIF datetime string to ISO 8601 format.

    EXIF datetime format: '2024:03:15 14:30:00'
    ISO 8601 format: '2024-03-15T14:30:00'

    Args:
        exif_datetime: EXIF datetime string

    Returns:
        ISO 8601 formatted datetime string or None if parsing fails
    """
    try:
        # Parse EXIF format
        dt = datetime.strptime(str(exif_datetime).strip(), "%Y:%m:%d %H:%M:%S")
        # Return ISO 8601 format
        return dt.isoformat()
    except (ValueError, AttributeError) as e:
        print(f"Warning: Failed to parse EXIF datetime '{exif_datetime}': {e}")
        return None


def _extract_gps_coordinates(gps_info: dict) -> Optional[dict]:
    """
    Extract GPS coordinates from EXIF GPSInfo.

    Args:
        gps_info: GPS information from EXIF

    Returns:
        Dictionary with latitude and longitude or None if extraction fails
    """
    try:
        # GPS tags
        gps_latitude = gps_info.get(2)  # GPSLatitude
        gps_latitude_ref = gps_info.get(1)  # GPSLatitudeRef (N/S)
        gps_longitude = gps_info.get(4)  # GPSLongitude
        gps_longitude_ref = gps_info.get(3)  # GPSLongitudeRef (E/W)

        if not all([gps_latitude, gps_latitude_ref, gps_longitude, gps_longitude_ref]):
            return None

        # Convert to decimal degrees
        lat = _convert_to_degrees(gps_latitude)
        if gps_latitude_ref == "S":
            lat = -lat

        lon = _convert_to_degrees(gps_longitude)
        if gps_longitude_ref == "W":
            lon = -lon

        return {"latitude": lat, "longitude": lon}

    except Exception as e:
        print(f"Warning: Failed to extract GPS coordinates: {e}")
        return None


def _convert_to_degrees(value: tuple) -> float:
    """
    Convert GPS coordinates from degrees/minutes/seconds to decimal degrees.

    Args:
        value: Tuple of (degrees, minutes, seconds)

    Returns:
        Decimal degrees
    """
    d, m, s = value
    return float(d) + float(m) / 60.0 + float(s) / 3600.0
