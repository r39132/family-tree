# WhatsApp Photo Import

The `import_whatsapp_photos.py` script imports photos from a WhatsApp chat export into the Family Tree album.

## Overview

This script:
- Parses WhatsApp chat export `_chat.txt` file to extract photo messages
- Matches photo filenames with actual files in the export folder
- Maps WhatsApp senders to Family Tree user IDs
- Uploads photos in bulk using the album API endpoint
- Preserves captions and metadata from the original messages

## Prerequisites

1. **WhatsApp Chat Export**: Export a WhatsApp group chat with media included
2. **Backend Server**: Running backend API (local or remote)
3. **Authentication**: Valid auth token for the API
4. **Python Packages**: `requests`, `python-dotenv` (already in project requirements)

## WhatsApp Export Format

WhatsApp exports chats in the following format:

```
WhatsApp Chat Export/
├── _chat.txt           # Chat history with timestamps and senders
├── IMG-20240101-WA0001.jpg
├── IMG-20240101-WA0002.jpg
└── ...
```

The `_chat.txt` file contains messages like:
```
[1/15/24, 3:45 PM] John Doe: IMG-20240101-WA0001.jpg
[1/15/24, 3:46 PM] Jane Smith: Check out this photo!
[1/15/24, 4:20 PM] John Doe: IMG-20240101-WA0002.jpg Family gathering 2024
```

## Usage

### Basic Usage

```bash
cd backend/scripts
python import_whatsapp_photos.py \
  --export-folder /path/to/whatsapp/export \
  --space-id karunakaran \
  --token YOUR_AUTH_TOKEN
```

### With Phone Mapping

Create a JSON file mapping WhatsApp sender names/numbers to Family Tree member IDs:

```json
{
  "John Doe": "member_id_abc123",
  "+1234567890": "member_id_xyz789",
  "Mom": "member_id_mom001"
}
```

Then run:

```bash
python import_whatsapp_photos.py \
  --export-folder /path/to/whatsapp/export \
  --space-id karunakaran \
  --mapping-file phone_mapping.json \
  --token YOUR_AUTH_TOKEN
```

### Dry Run (Test Without Uploading)

```bash
python import_whatsapp_photos.py \
  --export-folder /path/to/whatsapp/export \
  --space-id karunakaran \
  --dry-run
```

### Using Environment Variables

Set your auth token in `.env`:

```bash
export AUTH_TOKEN=your_token_here
```

Then run without `--token`:

```bash
python import_whatsapp_photos.py \
  --export-folder /path/to/whatsapp/export \
  --space-id karunakaran
```

## Command-Line Arguments

| Argument | Required | Default | Description |
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
