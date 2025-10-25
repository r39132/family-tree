# How to Import WhatsApp Photos to Family Tree Album

This guide walks you through importing photos from a WhatsApp family group chat into your Family Tree album.

## Quick Start (5 Steps)

### Step 1: Export Your WhatsApp Chat

**On iPhone:**
1. Open the WhatsApp family group chat
2. Tap the group name at the top
3. Scroll down and tap "Export Chat"
4. Select "Attach Media" (important!)
5. Choose how to save (email to yourself, save to Files, AirDrop, etc.)

**On Android:**
1. Open the WhatsApp family group chat
2. Tap the three dots menu (⋮)
3. Tap "More" → "Export chat"
4. Select "Include Media" (important!)
5. Choose how to save the export

You'll get a ZIP file or folder containing:
- `_chat.txt` - The chat history
- Image files like `IMG-20240101-WA0001.jpg`

### Step 2: Extract the Export

1. Transfer the export to your computer
2. Unzip if it's a ZIP file
3. Note the folder path (e.g., `/Users/yourname/Downloads/WhatsApp Chat - Family`)

### Step 3: Get Your Space ID

Your space ID is in the URL when you're viewing your family tree:
```
https://your-app.com/tree?space=karunakaran
                                ^^^^^^^^^^^
                                This is your space ID
```

Or ask your admin for the space ID.

### Step 4: Get Your Authentication Token

**Option A: From Browser DevTools (Easy)**
1. Log into Family Tree in your browser
2. Open DevTools (F12 or right-click → Inspect)
3. Go to Application/Storage → Cookies
4. Find the `access_token` cookie and copy its value

**Option B: From Login API**
```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"youruser","password":"yourpass"}' \
  | jq -r '.access_token'
```

### Step 5: Run the Import Script

```bash
cd backend/scripts

# Basic import (uses sender names as-is)
python import_whatsapp_photos.py \
  --export-folder "/Users/yourname/Downloads/WhatsApp Chat - Family" \
  --space-id karunakaran \
  --token "your_access_token_here"
```

**That's it!** The script will:
- ✅ Parse the chat history
- ✅ Find all photos
- ✅ Upload them to your album
- ✅ Preserve captions and dates
- ✅ Show you a summary when done

---

## Advanced: Map Senders to Family Members

To associate photos with the correct family members (instead of just WhatsApp names):

### 1. Create a Phone Mapping File

Create `phone_mapping.json`:

```json
{
  "Dad": "member_id_dad_abc123",
  "Mom": "member_id_mom_xyz789",
  "Siddharth Anand": "orTx8ZIGCxDYnB81uXKS",
  "+1234567890": "member_id_brother",
  "+919876543210": "member_id_sister"
}
```

**How to find member IDs:**

**Option A: From the URL when editing a member**
```
https://your-app.com/tree?space=karunakaran&editing=orTx8ZIGCxDYnB81uXKS
                                                     ^^^^^^^^^^^^^^^^^^^^
                                                     This is the member ID
```

**Option B: From Firestore Console**
1. Go to Firestore in Google Cloud Console
2. Open the `members` collection
3. Each document ID is a member ID

**Option C: Ask the script to show you**
```bash
# Run dry-run first to see sender names
python import_whatsapp_photos.py \
  --export-folder "/path/to/export" \
  --space-id karunakaran \
  --dry-run
```

This shows you all the sender names found in the chat, then you can map them.

### 2. Run Import with Mapping

```bash
python import_whatsapp_photos.py \
  --export-folder "/Users/yourname/Downloads/WhatsApp Chat - Family" \
  --space-id karunakaran \
  --mapping-file phone_mapping.json \
  --token "your_access_token_here"
```

---

## Testing Before Import (Dry Run)

Test the import without actually uploading anything:

```bash
python import_whatsapp_photos.py \
  --export-folder "/path/to/export" \
  --space-id karunakaran \
  --dry-run
```

This will show you:
- How many photos were found
- What senders were detected
- What would be uploaded

---

## Complete Example

Here's a real-world example:

```bash
# 1. Export WhatsApp chat from phone to Downloads/WhatsApp Chat - Family Group

# 2. Create phone mapping
cat > phone_mapping.json << 'EOF'
{
  "Siddharth Anand": "orTx8ZIGCxDYnB81uXKS",
  "Dad": "member_id_dad",
  "Mom": "member_id_mom",
  "+919876543210": "member_id_brother"
}
EOF

# 3. Test with dry-run
python import_whatsapp_photos.py \
  --export-folder "$HOME/Downloads/WhatsApp Chat - Family Group" \
  --space-id karunakaran \
  --mapping-file phone_mapping.json \
  --dry-run

# 4. Import for real
python import_whatsapp_photos.py \
  --export-folder "$HOME/Downloads/WhatsApp Chat - Family Group" \
  --space-id karunakaran \
  --mapping-file phone_mapping.json \
  --token "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."

# Output:
# Parsing WhatsApp chat export from: /Users/.../WhatsApp Chat - Family Group
# Found 127 photo messages in chat export
# Found 124 photo files in export folder
# Warning: Photo file not found: IMG-20240315-WA0055.jpg
# Warning: Photo file not found: IMG-20240415-WA0089.jpg
# Warning: Photo file not found: IMG-20240515-WA0103.jpg
# Prepared 124 photos for upload
#
# Upload complete:
#   Total: 124
#   Successful: 124
#   Failed: 0
#
# ✅ Successfully imported 124 photos!
```

---

## Troubleshooting

### "Chat file not found"
**Problem:** The script can't find `_chat.txt`

**Solution:** Make sure you're pointing to the correct folder and the export included the chat history.

### "Photo file not found" warnings
**Problem:** Some photos mentioned in the chat aren't in the folder

**Explanation:** This is normal! It happens when:
- Someone deleted a photo after sending it
- The export didn't include all media
- WhatsApp omitted some files

**Action:** The script will continue and import all available photos.

### "Authentication failed"
**Problem:** Your token is invalid or expired

**Solution:** Get a fresh token (tokens usually expire after 24 hours).

### "No photos to upload"
**Problem:** No photo messages found in chat

**Solution:**
- Make sure you exported "With Media"
- Check that `_chat.txt` contains messages with image filenames
- Try exporting again

### Photos show wrong uploader
**Problem:** Photos are attributed to WhatsApp names instead of family members

**Solution:** Create a `phone_mapping.json` file (see "Advanced" section above).

---

## What Gets Imported?

For each photo, the script preserves:

| Field | Source | Example |
|-------|--------|---------|
| **Photo File** | WhatsApp export | `IMG-20240101-WA0001.jpg` |
| **Caption** | WhatsApp message | "Family gathering 2024" |
| **Date** | WhatsApp timestamp | "1/15/24" |
| **Time** | WhatsApp timestamp | "3:45 PM" |
| **Uploader** | Mapped or WhatsApp sender | "Siddharth Anand" → member ID |
| **Original Filename** | WhatsApp filename | Preserved in metadata |

---

## Tips & Best Practices

### ✅ Do's
- **Test with dry-run first** to see what will be imported
- **Create a phone mapping** for accurate attribution
- **Export with media** to get the actual photos
- **Check the output** to see if any photos were skipped
- **Keep the export folder** until you verify the import worked

### ❌ Don'ts
- **Don't import duplicates** - The script doesn't check for duplicates
- **Don't use production tokens in scripts** - They might be logged
- **Don't delete the export** until you verify the upload
- **Don't forget to specify --space-id** or photos go to wrong space

---

## Need More Help?

- **Complete Documentation**: See [WHATSAPP_IMPORT.md](WHATSAPP_IMPORT.md) for full details
- **Script Reference**: See [BACKEND_SCRIPTS.md](BACKEND_SCRIPTS.md) for all scripts
- **Album Documentation**: See [FAMILY_ALBUM.md](FAMILY_ALBUM.md) for album features
- **Report Issues**: Create a GitHub issue if you encounter problems

---

## Summary

**Import WhatsApp photos in 3 commands:**

```bash
# 1. Export chat from WhatsApp (with media)

# 2. Test the import
python import_whatsapp_photos.py \
  --export-folder "/path/to/WhatsApp Chat - Family" \
  --space-id your_space_id \
  --dry-run

# 3. Import for real
python import_whatsapp_photos.py \
  --export-folder "/path/to/WhatsApp Chat - Family" \
  --space-id your_space_id \
  --token your_access_token
```

🎉 **Done!** Your family photos are now in the Family Tree album.
