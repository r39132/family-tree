# Family Album Feature Guide

## Overview

The Family Album feature allows family space members to upload, share, view, and interact with family photos. Each family space has its own isolated album with support for likes, tags, filtering, and sorting.

## Features

### Photo Management
- **Upload**: Drag-and-drop or file picker interface supporting JPEG, PNG, WebP, and GIF formats
- **Thumbnails**: Automatically generated (300x300px) for fast loading
- **Storage**: Photos stored in Google Cloud Storage with CDN support
- **Size Limit**: Configurable (default: 5MB per photo)
- **Batch Upload**: Upload multiple photos at once

### Photo Gallery
- **Responsive Grid**: Adaptive layout that works on desktop and mobile
- **Lazy Loading**: Photos load as you scroll for better performance
- **Hover Info**: See uploader name, upload date, and like count on hover
- **Click to View**: Opens full-size image in lightbox viewer

### Filtering & Sorting
- **Sort Options**:
  - Upload Date (newest/oldest first)
  - Likes (most/least liked)
  - Filename (alphabetical)
  - Uploader (group by uploader)
  
- **Filter Options**:
  - By Tags: Filter photos by one or more tags
  - Clear Filters: Easy reset to show all photos

### Photo Lightbox
- **Full-Size View**: View photos at original resolution
- **Navigation**: Use arrows or keyboard to browse through photos
- **Zoom**: Photos scale to fit screen while maintaining aspect ratio
- **Metadata**: View uploader, upload date, filename, dimensions
- **Close**: ESC key or click outside to close

### Social Features
- **Likes**: Like/unlike photos with visual feedback and count
- **Tags**: Add/edit tags on photos for organization
- **Comments**: (Future feature)

### Security & Access Control
- **Space Isolation**: Each family space has its own album
- **Member-Only Access**: Only authenticated space members can view/upload
- **Upload Permissions**: All space members can upload
- **Delete Permissions**: Only photo uploader can delete their photos
- **CDN Security**: Time-limited signed URLs (7-day expiration)

## Using the Family Album

### Accessing the Album
1. Log in to your family space
2. Click the "Album" button in the top navigation bar
3. You'll see the photo gallery for your current family space

### Uploading Photos
1. Click the "+ Upload Photos" button
2. Select one or more image files from your device
3. Supported formats: JPEG, PNG, WebP, GIF
4. Maximum file size: 5MB per photo (configurable)
5. Photos will upload and appear in the gallery automatically

### Viewing Photos
1. Click any photo thumbnail in the gallery
2. The photo opens in a lightbox viewer at full size
3. Use the arrow buttons or keyboard arrows to navigate
4. Click outside the photo or press ESC to close

### Liking Photos
1. Open a photo in the lightbox viewer
2. Click the heart button (❤️) to like/unlike
3. Like count updates immediately
4. Your likes are visible to all space members

### Adding Tags
1. Open a photo in the lightbox viewer
2. Enter tags in the "Add tags" input field (comma-separated)
3. Click "Update Tags" to save
4. Tags appear on photo thumbnails and can be used for filtering

### Filtering Photos
1. Use the "Filter by tags" input to enter tag names
2. Separate multiple tags with commas
3. Gallery shows only photos matching any of the tags
4. Click "Clear Filters" to see all photos again

### Sorting Photos
1. Use the sort dropdown to choose sort field:
   - Upload Date
   - Likes
   - Filename
   - Uploader
2. Use the order dropdown to choose ascending/descending
3. Gallery updates immediately

### Deleting Photos
1. Open a photo you uploaded in the lightbox viewer
2. Click the "Delete" button (only visible for your photos)
3. Confirm the deletion
4. Photo is permanently removed from storage and database

## Album Statistics

The album page displays helpful statistics:
- **Total Photos**: Total number of photos in the album
- **Total Likes**: Total likes across all photos
- **Recent Uploads**: Photos uploaded in the last 7 days

## Technical Details

### Storage
- **Original Photos**: Stored in GCS bucket at `{space-id}/originals/{photo-id}.jpg`
- **Thumbnails**: Stored in GCS bucket at `{space-id}/thumbnails/{photo-id}_thumb.jpg`
- **CDN**: Photos served via CDN for fast loading
- **Signed URLs**: Time-limited access tokens (7-day expiration)

### Database Schema

#### album_photos Collection
```javascript
{
  id: string,                    // Auto-generated UUID
  space_id: string,              // Family space ID
  uploader_id: string,           // User who uploaded
  filename: string,              // Original filename
  gcs_path: string,              // GCS object path
  thumbnail_path: string,        // Thumbnail GCS path
  cdn_url: string,               // CDN-served URL
  thumbnail_cdn_url: string,     // Thumbnail CDN URL
  upload_date: timestamp,        // Upload timestamp
  file_size: number,             // Size in bytes
  width: number,                 // Image width
  height: number,                // Image height
  mime_type: string,             // Image MIME type
  tags: array<string>,           // Photo tags
  created_at: timestamp,
  updated_at: timestamp
}
```

#### album_likes Collection
```javascript
{
  id: string,                    // Auto-generated
  photo_id: string,              // Reference to album_photos
  user_id: string,               // User who liked
  space_id: string,              // Family space ID
  created_at: timestamp
}
```

### API Endpoints

- `POST /spaces/{space_id}/album/photos` - Upload photo
- `GET /spaces/{space_id}/album/photos` - List photos (supports filters: uploader, tags, sort_by, sort_order, limit)
- `GET /spaces/{space_id}/album/photos/{photo_id}` - Get single photo
- `DELETE /spaces/{space_id}/album/photos/{photo_id}` - Delete photo
- `POST /spaces/{space_id}/album/photos/{photo_id}/like` - Like photo
- `DELETE /spaces/{space_id}/album/photos/{photo_id}/like` - Unlike photo
- `PUT /spaces/{space_id}/album/photos/{photo_id}/tags` - Update tags
- `GET /spaces/{space_id}/album/stats` - Get album statistics

### Configuration

The following environment variables configure the album feature:

```bash
# Album bucket name (required for photo storage)
ALBUM_BUCKET_NAME=my-project-family-albums

# Maximum upload size in MB (default: 5)
ALBUM_MAX_UPLOAD_SIZE_MB=5

# Thumbnail size in pixels (default: 300)
ALBUM_THUMBNAIL_SIZE=300

# CDN base URL (optional, uses signed URLs if not set)
CDN_BASE_URL=https://cdn.example.com

# Signed URL expiration in days (default: 7)
SIGNED_URL_EXPIRATION_DAYS=7
```

## Future Enhancements

- **Comments**: Add comment threads on photos
- **Albums**: Organize photos into sub-albums/collections
- **Slideshow**: Auto-play slideshow mode
- **Face Detection**: Auto-tag family members using ML
- **Photo Editing**: Basic filters, crop, rotate
- **Download Albums**: Bulk download as ZIP
- **Sharing**: Share album link with non-members
- **Search**: Full-text search in tags and metadata
- **Print Integration**: Order prints via third-party service

## Troubleshooting

### Photos not uploading
- Check file size (must be under 5MB by default)
- Verify file format (JPEG, PNG, WebP, GIF only)
- Check browser console for error messages
- Ensure you have permission to upload to the space

### Photos not displaying
- Verify GCS bucket is configured correctly
- Check that CDN URLs are accessible
- Ensure signed URLs haven't expired (regenerate after 7 days)
- Check browser console for CORS errors

### Unable to delete photos
- Only the photo uploader can delete their photos
- Ensure you're logged in with the correct account
- Check that the photo still exists in the database

### Performance issues
- Enable CDN for faster photo loading
- Use thumbnail URLs for gallery views
- Consider implementing lazy loading for large albums
- Optimize images before uploading (use reasonable resolution)

## Support

For issues or questions about the Family Album feature, please:
1. Check the troubleshooting section above
2. Review the backend logs for error messages
3. Open an issue on the GitHub repository
