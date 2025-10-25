#!/usr/bin/env python3
"""
Simple WhatsApp Photo Importer

Uploads all photos from a WhatsApp export folder to the Family Tree album.
Uses the bulk upload endpoint for efficient batch processing.

Usage:
    python import_whatsapp_photos.py --export-folder <path> --space-id <space_id> --token <token>
"""

import argparse
import sys
from pathlib import Path
from typing import List

try:
    import requests
except ImportError:
    print("Error: requests package not installed. Run: pip install requests")
    sys.exit(1)


def find_photos(export_folder: Path) -> List[Path]:
    """Find all .jpg and .jpeg files in the export folder."""
    photos = []

    # Common WhatsApp photo patterns
    for pattern in ["*.jpg", "*.jpeg", "*.JPG", "*.JPEG"]:
        photos.extend(export_folder.glob(pattern))

    # Sort by filename for consistent ordering
    photos.sort()

    return photos


def upload_photos(
    space_id: str, photo_files: List[Path], api_url: str, token: str, dry_run: bool = False
):
    """Upload photos to the album using the bulk endpoint."""

    if not photo_files:
        print("❌ No photos found to upload")
        return

    print(f"📸 Found {len(photo_files)} photos to upload")

    if dry_run:
        print("\n🔍 DRY RUN MODE - No uploads will be performed")
        print("\nPhotos that would be uploaded:")
        for i, photo in enumerate(photo_files, 1):
            print(f"  {i}. {photo.name} ({photo.stat().st_size / 1024:.1f} KB)")
        return

    # Prepare files for upload
    print("\n📤 Uploading photos...")
    files = []
    file_handles = []

    try:
        for photo in photo_files:
            fh = open(photo, "rb")
            file_handles.append(fh)
            files.append(("files", (photo.name, fh, "image/jpeg")))

        # Make API request
        url = f"{api_url}/spaces/{space_id}/album/photos/bulk"
        headers = {"Authorization": f"Bearer {token}"}

        response = requests.post(url, files=files, headers=headers, timeout=300)
        response.raise_for_status()
        result = response.json()

        # Display results
        print("\n✅ Upload complete!")
        print(f"   Total: {result.get('total', 0)}")
        print(f"   Successful: {result.get('successful', 0)}")
        print(f"   Failed: {result.get('failed', 0)}")

        if result.get("errors"):
            print("\n⚠️  Errors encountered:")
            for error in result["errors"]:
                print(f"   - {error}")

        if result.get("successful", 0) > 0:
            print(f"\n🎉 Successfully imported {result['successful']} photos!")

    except requests.exceptions.RequestException as e:
        print(f"\n❌ Upload failed: {e}")
        if hasattr(e, "response") and e.response is not None:
            try:
                error_detail = e.response.json()
                print(f"   Error details: {error_detail}")
            except Exception:
                print(f"   Response: {e.response.text}")
        sys.exit(1)
    finally:
        # Close all file handles
        for fh in file_handles:
            fh.close()


def main():
    parser = argparse.ArgumentParser(
        description="Import all photos from WhatsApp export folder to Family Tree album"
    )
    parser.add_argument(
        "--export-folder", required=True, help="Path to WhatsApp export folder containing photos"
    )
    parser.add_argument("--space-id", required=True, help="Family space ID to upload photos to")
    parser.add_argument("--token", required=True, help="Authentication token")
    parser.add_argument(
        "--api-url",
        default="http://localhost:8000",
        help="Backend API base URL (default: http://localhost:8000)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be uploaded without actually uploading",
    )

    args = parser.parse_args()

    # Validate export folder
    export_folder = Path(args.export_folder)
    if not export_folder.exists():
        print(f"❌ Error: Export folder not found: {export_folder}")
        sys.exit(1)

    if not export_folder.is_dir():
        print(f"❌ Error: Not a directory: {export_folder}")
        sys.exit(1)

    # Find photos
    print(f"�� Scanning for photos in: {export_folder}")
    photos = find_photos(export_folder)

    if not photos:
        print("❌ No photos found in export folder")
        sys.exit(1)

    # Upload photos
    upload_photos(
        space_id=args.space_id,
        photo_files=photos,
        api_url=args.api_url,
        token=args.token,
        dry_run=args.dry_run,
    )


if __name__ == "__main__":
    main()
