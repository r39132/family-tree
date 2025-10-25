# WhatsApp Photo Import

Import photos from WhatsApp chat exports into your Family Tree album.

## Quick Start

### 1. Export WhatsApp Chat

**iPhone/Android/Desktop**: Open chat → Export Chat → **Include Media**

You'll get a ZIP file containing `_chat.txt` and image files.

### 2. Extract & Note Path

Unzip the export and note the folder path:
- macOS: `/Users/yourname/Downloads/WhatsApp Chat - Family`
- Windows: `C:\Users\yourname\Downloads\WhatsApp Chat - Family`

### 3. Get Auth Token

Open browser DevTools (F12) → Application → Local Storage → copy `token` value

Or via API:
```bash
curl -X POST http://localhost:8080/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"user","password":"pass"}' | jq -r '.access_token'
```

### 4. Run Import

```bash
cd backend/scripts

python import_whatsapp_photos.py \
  --export-folder "/path/to/WhatsApp Chat - Family" \
  --space-id your_space_id \
  --token "your_token_here"
```

**Windows PowerShell**: Use backticks `` ` `` for line continuation
**Windows CMD**: Put all on one line

## Features

- ✅ **Duplicate Detection**: Skips already-uploaded photos (by filename)
- ✅ **Bulk Upload**: Uploads all photos via bulk endpoint
- ✅ **Progress Tracking**: Shows upload progress and summary
- ✅ **Dry Run**: Test without uploading (`--dry-run` flag)
- ✅ **Error Handling**: Continues on errors, reports failures

## Command-Line Options

| Option | Required | Description |
|--------|----------|-------------|
| `--export-folder` | Yes | Path to WhatsApp export folder |
| `--space-id` | Yes | Family space ID |
| `--token` | Yes* | Auth token (*or set in `.env`) |
| `--api-url` | No | API base URL (default: `http://localhost:8080`) |
| `--dry-run` | No | Test mode, no uploads |

## Example Output

```
📸 Scanning for photos in: /Users/me/WAK
📸 Found 12 photos in export folder
🔍 Checking for existing photos in album...
   Found 9 existing photos

📊 Upload Summary:
   Total photos in folder: 12
   Already uploaded (skipped): 9
   New photos to upload: 3

⏭️  Skipping duplicates:
   - IMG-20251019-WA0010.jpg
   - IMG-20251019-WA0011.jpg
   ...

📤 Uploading 3 new photos...
✅ Upload complete!
   Total: 3
   Successful: 3
   Failed: 0

🎉 Successfully imported 3 photos!
```

## Troubleshooting

- **"No photos found"**: Ensure export folder contains `.jpg`/`.jpeg` files
- **"401 Unauthorized"**: Token expired, get a fresh one
- **"Connection refused"**: Backend not running or wrong API URL
- **"Access denied"**: Check you have permission for the space

## Technical Details

**What it does**:
1. Scans export folder for all `.jpg` and `.jpeg` files
2. Fetches existing photos from album API
3. Compares filenames to identify duplicates
4. Uploads only new photos via bulk endpoint
5. Reports results (success/failure counts)

**Script location**: `backend/scripts/import_whatsapp_photos.py`
**Dependencies**: `requests` library (already in requirements)
|----------|----------|---------|-------------|
| `--export-folder` | Yes | - | Path to WhatsApp chat export folder |
| `--space-id` | Yes | - | Space ID to upload photos to |
| `--mapping-file` | No | - | JSON file mapping senders to user IDs |
| `--api-url` | No | `http://localhost:8000` | Backend API base URL |
| `--token` | No | - | Auth token (or use `AUTH_TOKEN` env var) |
| `--dry-run` | No | `false` | Parse and prepare but don't upload |

## Phone Mapping File

The phone mapping file should be a JSON object where:
- **Keys**: Sender names or phone numbers as they appear in WhatsApp
- **Values**: Family Tree member IDs

Example (`phone_mapping.json`):

```json
{
  "Siddharth Anand": "orTx8ZIGCxDYnB81uXKS",
  "+919876543210": "member_id_relative1",
  "Dad": "member_id_dad",
  "Mom": "member_id_mom"
}
```

If no mapping file is provided, the script will use the WhatsApp sender names as-is for the `uploaded_by` field.

## Output

The script provides progress updates and a summary:

```
Parsing WhatsApp chat export from: /path/to/export
Found 45 photo messages in chat export
Found 42 photo files in export folder
Warning: Photo file not found: IMG-20240101-WA0003.jpg
Prepared 42 photos for upload

Upload complete:
  Total: 42
  Successful: 40
  Failed: 2

Errors:
  - IMG-20240101-WA0025.jpg: File size exceeds limit
  - IMG-20240101-WA0031.jpg: Invalid image format

✅ Successfully imported 40 photos!
```

## Features

### Supported WhatsApp Message Formats

The script handles various WhatsApp message formats:
- `[1/15/24, 3:45 PM] Sender: IMG-20240101-WA0001.jpg`
- `1/15/24, 3:45 PM - Sender: IMG-20240101-WA0001.jpg`
- Messages with 12-hour (AM/PM) or 24-hour time formats
- Multi-line captions
- `<Media omitted>` placeholders

### Photo Filename Patterns

Supports WhatsApp photo naming conventions:
- `IMG-YYYYMMDD-WA####.jpg`
- `IMG-YYYYMMDD-WA####.jpeg`
- Other media patterns with WA prefix

### Metadata Preservation

For each photo, the script preserves:
- Original filename
- Upload date and time
- Sender information
- Message caption (if any)

## Limitations

1. **Photo Files Only**: Currently only imports `.jpg`/`.jpeg` files (photos). Videos and other media are not supported.
2. **Caption Length**: Very long captions may be truncated by the API
3. **File Size**: Photos must meet the backend size limits (default: 10MB)
4. **Duplicates**: The script doesn't detect duplicates; photos will be uploaded even if they already exist

## Troubleshooting

### "Chat file not found"
Ensure the export folder contains `_chat.txt`. Some WhatsApp exports may use a different filename.

### "Photo file not found" warnings
The chat log references a photo that wasn't included in the export. This can happen if:
- Media was excluded during export
- File was deleted after export
- Filename format doesn't match expected pattern

### "Authentication token required"
Provide a valid token via `--token` argument or `AUTH_TOKEN` environment variable.

### Upload failures
Check:
- Backend server is running
- File sizes are within limits
- Image files are valid JPEGs
- Network connectivity

## Integration with seed_demo_album.py

This script is designed to replace `seed_demo_album.py` for real WhatsApp data. Key differences:

| Feature | seed_demo_album.py | import_whatsapp_photos.py |
|---------|-------------------|--------------------------|
| Data source | Hardcoded test data | Real WhatsApp exports |
| Captions | Generated | Preserved from messages |
| Uploaders | Random/hardcoded | Mapped from senders |
| Dates | Current date | Original message dates |
| Use case | Development/testing | Production data import |

## Example Workflow

1. **Export WhatsApp Chat**: On your phone, export the family WhatsApp group with media
2. **Transfer to Computer**: Copy the export folder to your computer
3. **Create Phone Mapping**: Map WhatsApp names to member IDs
4. **Test with Dry Run**: Verify parsing works correctly
5. **Import Photos**: Run the script to upload photos
6. **Verify in App**: Check the album in the Family Tree app

```bash
# 1. Test parsing
python import_whatsapp_photos.py \
  --export-folder ~/Downloads/WhatsApp\ Chat\ -\ Family \
  --space-id karunakaran \
  --dry-run

# 2. Import photos
python import_whatsapp_photos.py \
  --export-folder ~/Downloads/WhatsApp\ Chat\ -\ Family \
  --space-id karunakaran \
  --mapping-file phone_mapping.json \
  --token $AUTH_TOKEN
```

## Future Enhancements

Potential improvements for future versions:
- Video support
- Duplicate detection using file hashes
- Resume capability for interrupted uploads
- Progress bar for large imports
- Automatic date parsing and timezone handling
- Support for other chat export formats (Telegram, etc.)
