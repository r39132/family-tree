# Family Album Feature

## Overview

The Family Album feature allows family space members to upload, share, view, and interact with family photos. Each family space has its own isolated album.

## Features

- **Upload Photos**: Drag-and-drop or file picker (JPEG, PNG, WebP, GIF up to 5MB)
- **Bulk Operations**: Upload/delete multiple photos with progress tracking
- **Photo Gallery**: Responsive grid with thumbnails and lightbox viewer
- **Social Features**: Like photos and add tags for organization
- **Filtering & Sorting**: Sort by date/likes/name, filter by tags
- **WhatsApp Import**: Import photos from WhatsApp chat exports ([guide](WHATSAPP_IMPORT.md))

## Quick Usage

1. **Access**: Click "Album" in the top navigation bar
2. **Upload**: Click "+ Upload Photos" and select files
3. **View**: Click any photo to open full-size lightbox
4. **Like**: Click ❤️ button in lightbox
5. **Tag**: Enter tags (comma-separated) and click "Update Tags"
6. **Delete**:
   - Individual: Click "Delete" in lightbox (your photos only)
   - Bulk: Click "Select Photos" → select multiple → "Delete"

## Album Statistics

- **Total Photos**: Total count in album
- **Total Likes**: Likes across all photos
- **Recent Uploads**: Photos uploaded in last 7 days

## Configuration

Environment variables:

```bash
ALBUM_BUCKET_NAME=my-project-album-photos  # Required
ALBUM_MAX_UPLOAD_SIZE_MB=10                # Default: 10
ALBUM_THUMBNAIL_SIZE=300                   # Default: 300
SIGNED_URL_EXPIRATION_DAYS=7               # Default: 7
```

## Technical Details

### Storage Structure
- Originals: `{space-id}/originals/{photo-id}.jpg`
- Thumbnails: `{space-id}/thumbnails/{photo-id}_thumb.jpg`
- Access: Private bucket with 7-day signed URLs

### API Endpoints
- `POST /spaces/{space_id}/album/photos` - Upload photo
- `POST /spaces/{space_id}/album/photos/bulk` - Bulk upload
- `POST /spaces/{space_id}/album/photos/bulk-delete` - Bulk delete
- `GET /spaces/{space_id}/album/photos` - List photos (with filters)
- `DELETE /spaces/{space_id}/album/photos/{photo_id}` - Delete photo
- `POST /spaces/{space_id}/album/photos/{photo_id}/like` - Like/unlike
- `PUT /spaces/{space_id}/album/photos/{photo_id}/tags` - Update tags
- `GET /spaces/{space_id}/album/stats` - Get statistics

### Database Schema

**album_photos**:
```javascript
{
  id, space_id, uploader_id, filename,
  gcs_path, thumbnail_path, cdn_url, thumbnail_cdn_url,
  upload_date, file_size, width, height,
  mime_type, tags[], created_at, updated_at
}
```

**album_likes**:
```javascript
{
  id, photo_id, user_id, space_id, created_at
}
```

## Troubleshooting

- **Photos not uploading**: Check file size/format, verify bucket permissions
- **Photos not displaying**: Verify signed URLs haven't expired, check CORS
- **Can't delete**: Only uploader can delete their photos
- **Performance**: Use thumbnails for gallery, enable CDN

For more help, check backend logs or open a GitHub issue.
