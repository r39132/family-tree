# Profile Pictures

This document explains how to set up and use the profile picture upload feature in the Family Tree application.

## Overview

The profile picture feature allows users to upload and display profile pictures for family tree members. Images are automatically optimized and stored securely in Google Cloud Storage with signed URLs for private access.

## Features

- **File Upload:** Drag-and-drop or click to select images
- **Format Support:** JPEG, PNG, and WebP formats
- **Automatic Optimization:**
  - Images resized to max 800x800 pixels
  - Converted to JPEG format
  - Compressed for optimal web delivery
  - Transparent backgrounds converted to white
- **Size Limit:** Configurable (default 5MB)
- **Preview:** Circular preview before and after upload
- **Security:**
  - Requires authentication and member access validation
  - Private bucket with signed URLs (no public access)
  - URLs valid for 7 days, automatically refreshed
- **No Placeholder:** Shows no avatar when picture doesn't exist (clean appearance)

## Setup

### 1. Create Google Cloud Storage Bucket

```bash
# Set your project ID
PROJECT_ID="your-project-id"

# Create bucket (replace with your project ID)
gsutil mb -p $PROJECT_ID -l us-central1 gs://${PROJECT_ID}-profile-pictures

# Enable uniform bucket-level access (modern IAM approach)
gsutil uniformbucketlevelaccess set on gs://${PROJECT_ID}-profile-pictures

# Grant service account storage permissions
# Replace with your service account email
gsutil iam ch serviceAccount:family-tree-runtime@${PROJECT_ID}.iam.gserviceaccount.com:objectAdmin gs://${PROJECT_ID}-profile-pictures
```

**Important Security Notes:**
- ⚠️ **No public access required** - Uses signed URLs for secure image access
- ⚠️ **Private bucket** - Only the service account has access
- ✅ **Signed URLs** - Images accessible via time-limited signed URLs (7 days)

**Bucket Naming Convention:** `{project-id}-profile-pictures`

**Example:** If your project ID is `family-tree-469815`, use bucket name: `family-tree-469815-profile-pictures`

### 2. Configure Environment Variables

Add to `backend/.env`:

```bash
# Required: Cloud Storage bucket name
GCS_BUCKET_NAME=your-project-id-profile-pictures

# Optional: Maximum upload size in MB (default: 5)
MAX_UPLOAD_SIZE_MB=5
```

Example:
```bash
GCS_BUCKET_NAME=family-tree-469815-profile-pictures
MAX_UPLOAD_SIZE_MB=5
```

### 3. Install Dependencies

The required dependencies are included in `pyproject.toml`:
- `google-cloud-storage>=2.14.0` - Cloud Storage client
- `pillow>=10.0.0` - Image processing
- `python-multipart>=0.0.6` - File upload handling

Install with:
```bash
cd backend
uv sync
```

### 4. Verify Setup

Test that the configuration works:

```bash
cd backend
uv run python -c "from app.storage import get_storage_client; print('✅ Storage configured' if get_storage_client() else '❌ GCS_BUCKET_NAME not set')"
```

## Usage

### Uploading Profile Pictures

1. **Edit a Member:** Click the edit button on any family tree member
2. **Select Image:**
   - Click "Choose File" button
   - Or drag and drop an image onto the file picker
3. **Preview:** The selected image will show as a circular preview
4. **Upload:** Click "Upload Picture" button
5. **Save:** Click "Save" to save the member with the new profile picture URL

### Supported Formats

- **JPEG** (.jpg, .jpeg)
- **PNG** (.png)
- **WebP** (.webp)

### Size Limits

- **Maximum file size:** 5MB (configurable via `MAX_UPLOAD_SIZE_MB`)
- **Recommended dimensions:** 500x500 to 1000x1000 pixels
- **Automatic optimization:** Images larger than 800x800 are resized

### Best Practices

1. **Use square images** for best circular display
2. **Good lighting** ensures clear recognition
3. **High contrast** backgrounds work better
4. **Center the face** in the image
5. **Avoid very large files** to save upload time

## API Reference

### Upload Endpoint

**POST** `/tree/members/{member_id}/picture`

**Authentication:** Required (Bearer token)

**Request:**
- Content-Type: `multipart/form-data`
- Body: Form field named `file` containing the image

**Response:**
```json
{
  "profile_picture_url": "https://storage.googleapis.com/...",
  "message": "Profile picture uploaded successfully"
}
```

**Error Responses:**
- `400` - Invalid file type or size
- `403` - User doesn't have access to this member
- `404` - Member not found
- `500` - Upload failed
- `501` - Cloud Storage not configured

**Example cURL:**
```bash
curl -X POST \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@/path/to/image.jpg" \
  https://your-api.run.app/tree/members/MEMBER_ID/picture
```

## Technical Details

### Image Processing Pipeline

1. **Validation:**
   - Check file type (JPEG/PNG/WebP only)
   - Check file size (max 5MB default)
   - Verify user has access to member

2. **Optimization:**
   - Open image with Pillow
   - Convert RGBA/LA/P modes to RGB
   - Replace transparent backgrounds with white
   - Resize to max 800x800 (maintains aspect ratio)
   - Save as JPEG with 85% quality

3. **Storage:**
   - Generate unique filename: `profile-pictures/{member_id}/{uuid}.jpg`
   - Upload to Google Cloud Storage
   - Generate signed URL (valid for 7 days)
   - Return signed URL

4. **Update:**
   - Delete old picture from GCS (if exists)
   - Update member's `profile_picture_url` in Firestore with signed URL

### Storage Structure

```
gs://your-bucket-name/
└── profile-pictures/
    ├── {member-id-1}/
    │   ├── {uuid-1}.jpg
    │   └── {uuid-2}.jpg
    └── {member-id-2}/
        └── {uuid-3}.jpg
```

### Security Considerations

- **Authentication Required:** All uploads require valid JWT token
- **Access Control:** Users can only upload for members in their space
- **File Validation:** Server-side validation of file types and sizes
- **Private Storage:** Bucket is private, no public access granted
- **Signed URLs:** Time-limited URLs (7 days) for secure image access
- **Automatic Refresh:** Application regenerates signed URLs when needed
- **Unique Filenames:** UUID prevents filename collisions
- **Old File Cleanup:** Previous pictures are deleted on new upload

## Troubleshooting

### "Image upload is not configured"

**Cause:** `GCS_BUCKET_NAME` environment variable not set

**Solution:** Add `GCS_BUCKET_NAME=your-bucket-name` to `backend/.env`

### "Failed to upload image"

**Possible Causes:**
1. Bucket doesn't exist
2. Service account lacks permissions
3. Invalid bucket name

**Solution:**
```bash
# Verify bucket exists
gsutil ls gs://your-bucket-name

# Check permissions
gcloud projects get-iam-policy your-project-id

# Ensure service account has Storage Object Creator role
```

### "Images not displaying"

**Cause:** Signed URL expired (after 7 days) or invalid

**Solution:**
- Application automatically regenerates signed URLs when needed
- If images still don't display, check service account has `objectAdmin` role:
```bash
gsutil iam get gs://your-bucket-name
```

### "File too large" errors

**Solution:** Either:
- Resize the image before uploading
- Increase `MAX_UPLOAD_SIZE_MB` in backend/.env

### Development (Local) Errors

**Cause:** Not authenticated with GCP

**Solution:**
```bash
gcloud auth application-default login
```

## Cost Considerations

**Google Cloud Storage Pricing:**
- **Storage:** ~$0.02/GB/month (Standard storage, us-central1)
- **Operations:**
  - Upload (Class A): $0.05 per 10,000 operations
  - View (Class B): $0.004 per 10,000 operations
- **Network:** Free for same-region access

**Example Cost Estimates:**
- 100 profile pictures (~10MB each) = 1GB = **~$0.02/month**
- 1,000 pictures (1GB) + 10,000 views/month = **~$0.06/month**
- Very low cost for typical family tree usage

## Future Enhancements

Potential improvements for future versions:

- [ ] Drag-and-drop upload in member editor
- [ ] Image cropping tool before upload
- [ ] Batch upload for multiple members
- [ ] Thumbnail generation for faster loading
- [ ] CDN integration for global delivery
- [ ] Alternative storage backends (AWS S3, Azure Blob)
- [ ] Image rotation/editing tools
- [ ] Profile picture history/rollback

## Related Documentation

- [Deployment Guide](FORKED_DEPLOYMENT.md) - Cloud deployment setup
- [Architecture Overview](ARCHITECTURE.md) - System architecture
- [Backend Scripts](BACKEND_SCRIPTS.md) - Utility scripts reference
