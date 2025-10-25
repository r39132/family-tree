#!/usr/bin/env python3
"""
Seed demo family album with stock photos.

This script adds 10 placeholder photos to the demo family space album.
If ALBUM_BUCKET_NAME is configured, it will upload actual images to GCS.
Otherwise, it will use placeholder URLs (for development).
"""

import io
import os
import sys
from datetime import datetime, timedelta, timezone

from PIL import Image, ImageDraw, ImageFont

# Add parent directory to path to import app modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.config import settings
from app.firestore_client import get_db

# Try to import album functions, but don't fail if GCS is not configured
try:
    from app.album import upload_album_photo

    HAS_GCS = bool(settings.album_bucket_name)
except Exception as e:
    print(f"Note: GCS not available ({e}), will use placeholder URLs")
    HAS_GCS = False


def create_placeholder_image(width: int, height: int, color: tuple, text: str) -> bytes:
    """
    Create a placeholder image with text.

    Args:
        width: Image width
        height: Image height
        color: RGB color tuple
        text: Text to display on image

    Returns:
        Image as bytes
    """
    # Create image
    image = Image.new("RGB", (width, height), color)
    draw = ImageDraw.Draw(image)

    # Try to load a nice font, fall back to default
    try:
        font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 60)
    except OSError:
        font = ImageFont.load_default()

    # Calculate text position (centered)
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    position = ((width - text_width) // 2, (height - text_height) // 2)

    # Draw text
    draw.text(position, text, fill=(255, 255, 255), font=font)

    # Convert to bytes
    output = io.BytesIO()
    image.save(output, format="JPEG", quality=95)
    return output.getvalue()


def seed_album_photos():
    """Seed the demo family album with 10 stock photos."""
    db = get_db()

    # Photo data
    photos = [
        {
            "color": (52, 152, 219),  # Blue
            "text": "Family\nGathering",
            "tags": ["family", "gathering", "2024"],
            "uploader": "admin",
        },
        {
            "color": (46, 204, 113),  # Green
            "text": "Summer\nVacation",
            "tags": ["vacation", "summer", "beach"],
            "uploader": "admin",
        },
        {
            "color": (155, 89, 182),  # Purple
            "text": "Birthday\nParty",
            "tags": ["birthday", "celebration", "party"],
            "uploader": "admin",
        },
        {
            "color": (241, 196, 15),  # Yellow
            "text": "Wedding\nDay",
            "tags": ["wedding", "celebration", "2023"],
            "uploader": "admin",
        },
        {
            "color": (230, 126, 34),  # Orange
            "text": "Holiday\nDinner",
            "tags": ["holiday", "dinner", "family"],
            "uploader": "admin",
        },
        {
            "color": (231, 76, 60),  # Red
            "text": "Graduation",
            "tags": ["graduation", "school", "achievement"],
            "uploader": "admin",
        },
        {
            "color": (26, 188, 156),  # Turquoise
            "text": "Reunion",
            "tags": ["reunion", "family", "gathering"],
            "uploader": "admin",
        },
        {
            "color": (52, 73, 94),  # Dark Blue
            "text": "Anniversary",
            "tags": ["anniversary", "celebration", "love"],
            "uploader": "admin",
        },
        {
            "color": (142, 68, 173),  # Purple
            "text": "New Year",
            "tags": ["newyear", "celebration", "2024"],
            "uploader": "admin",
        },
        {
            "color": (22, 160, 133),  # Sea Green
            "text": "Picnic\nDay",
            "tags": ["picnic", "outdoor", "fun"],
            "uploader": "admin",
        },
    ]

    print(f"🌳 Seeding demo family album with {len(photos)} photos...")

    for i, photo_data in enumerate(photos, 1):
        try:
            # Create placeholder image
            image_content = create_placeholder_image(
                width=1200, height=800, color=photo_data["color"], text=photo_data["text"]
            )

            # Upload to GCS
            print(
                f"  [{i}/{len(photos)}] Uploading '{photo_data['text'].replace(chr(10), ' ')}'..."
            )
            upload_result = upload_album_photo(image_content, "image/jpeg", "demo")

            if not upload_result:
                print(f"    ❌ Failed to upload photo {i}")
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

            # Calculate upload date (spread over the last 3 months)
            days_ago = i * 9  # Spread 10 photos over ~90 days
            upload_date = (datetime.now(timezone.utc) - timedelta(days=days_ago)).isoformat()

            # Save to Firestore
            photo_doc = {
                "space_id": "demo",
                "uploader_id": photo_data["uploader"],
                "filename": f"demo_photo_{i}.jpg",
                "gcs_path": gcs_path,
                "thumbnail_path": thumbnail_path,
                "cdn_url": cdn_url,
                "thumbnail_cdn_url": thumbnail_cdn_url,
                "upload_date": upload_date,
                "file_size": len(image_content),
                "width": width,
                "height": height,
                "mime_type": "image/jpeg",
                "tags": photo_data["tags"],
                "created_at": upload_date,
                "updated_at": upload_date,
            }

            photo_ref = db.collection("album_photos").document(photo_id)
            photo_ref.set(photo_doc)

            print(f"    ✅ Uploaded: {photo_id}")

        except Exception as e:
            print(f"    ❌ Error uploading photo {i}: {e}")
            continue

    print("\n✅ Successfully seeded demo album with photos!")


if __name__ == "__main__":
    seed_album_photos()
