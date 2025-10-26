"""Tests for EXIF metadata extraction."""

import io
from datetime import datetime

import pytest
from PIL import Image
from PIL.ExifTags import TAGS

from app.utils.exif import (
    _convert_to_degrees,
    _extract_gps_coordinates,
    _parse_exif_datetime,
    extract_exif_metadata,
)


def create_test_image_with_exif(width=800, height=600, exif_data=None):
    """Create a test image with EXIF data."""
    img = Image.new("RGB", (width, height), color="red")

    if exif_data:
        exif_dict = img.getexif()
        for tag_name, value in exif_data.items():
            # Get tag ID from tag name
            tag_id = None
            for id, name in TAGS.items():
                if name == tag_name:
                    tag_id = id
                    break
            if tag_id:
                exif_dict[tag_id] = value
        img_bytes = io.BytesIO()
        img.save(img_bytes, format="JPEG", exif=exif_dict)
    else:
        img_bytes = io.BytesIO()
        img.save(img_bytes, format="JPEG")

    img_bytes.seek(0)
    return Image.open(img_bytes)


def test_extract_exif_metadata_no_exif():
    """Test extracting metadata from image without EXIF data."""
    img = create_test_image_with_exif()
    metadata = extract_exif_metadata(img)

    assert metadata["photo_date"] is None
    assert metadata["camera_make"] is None
    assert metadata["camera_model"] is None
    assert metadata["gps_latitude"] is None
    assert metadata["gps_longitude"] is None


def test_extract_exif_metadata_with_datetime():
    """Test extracting DateTimeOriginal from EXIF."""
    img = create_test_image_with_exif(exif_data={"DateTimeOriginal": "2024:03:15 14:30:00"})
    metadata = extract_exif_metadata(img)

    assert metadata["photo_date"] == "2024-03-15T14:30:00"


def test_extract_exif_metadata_with_camera_info():
    """Test extracting camera make and model from EXIF."""
    img = create_test_image_with_exif(
        exif_data={
            "Make": "Apple",
            "Model": "iPhone 14 Pro",
        }
    )
    metadata = extract_exif_metadata(img)

    assert metadata["camera_make"] == "Apple"
    assert metadata["camera_model"] == "iPhone 14 Pro"


def test_parse_exif_datetime_valid():
    """Test parsing valid EXIF datetime."""
    result = _parse_exif_datetime("2024:03:15 14:30:00")
    assert result == "2024-03-15T14:30:00"


def test_parse_exif_datetime_invalid():
    """Test parsing invalid EXIF datetime."""
    result = _parse_exif_datetime("invalid")
    assert result is None


def test_parse_exif_datetime_empty():
    """Test parsing empty EXIF datetime."""
    result = _parse_exif_datetime("")
    assert result is None


def test_convert_to_degrees():
    """Test converting GPS coordinates to decimal degrees."""
    # 37 degrees, 30 minutes, 0 seconds = 37.5 degrees
    result = _convert_to_degrees((37, 30, 0))
    assert result == 37.5

    # 122 degrees, 25 minutes, 30 seconds = 122.425 degrees
    result = _convert_to_degrees((122, 25, 30))
    assert abs(result - 122.425) < 0.001


def test_extract_gps_coordinates_valid():
    """Test extracting valid GPS coordinates."""
    gps_info = {
        1: "N",  # GPSLatitudeRef
        2: (37, 30, 0),  # GPSLatitude (37.5 N)
        3: "W",  # GPSLongitudeRef
        4: (122, 25, 30),  # GPSLongitude (122.425 W)
    }

    result = _extract_gps_coordinates(gps_info)
    assert result is not None
    assert abs(result["latitude"] - 37.5) < 0.001
    assert abs(result["longitude"] - (-122.425)) < 0.001


def test_extract_gps_coordinates_southern_hemisphere():
    """Test extracting GPS coordinates from southern hemisphere."""
    gps_info = {
        1: "S",  # GPSLatitudeRef
        2: (34, 0, 0),  # GPSLatitude (34 S)
        3: "E",  # GPSLongitudeRef
        4: (18, 0, 0),  # GPSLongitude (18 E)
    }

    result = _extract_gps_coordinates(gps_info)
    assert result is not None
    assert result["latitude"] == -34.0
    assert result["longitude"] == 18.0


def test_extract_gps_coordinates_missing_data():
    """Test extracting GPS coordinates with missing data."""
    gps_info = {
        1: "N",  # GPSLatitudeRef
        # Missing GPSLatitude
    }

    result = _extract_gps_coordinates(gps_info)
    assert result is None


def test_extract_exif_metadata_full():
    """Test extracting all EXIF metadata fields."""
    img = create_test_image_with_exif(
        exif_data={
            "DateTimeOriginal": "2024:03:15 14:30:00",
            "Make": "Canon",
            "Model": "EOS R5",
        }
    )

    metadata = extract_exif_metadata(img)

    assert metadata["photo_date"] == "2024-03-15T14:30:00"
    assert metadata["camera_make"] == "Canon"
    assert metadata["camera_model"] == "EOS R5"
