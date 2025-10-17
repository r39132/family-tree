# Bulk Upload Feature

## Overview

The Bulk Upload feature allows you to upload multiple family members at once using a JSON file. This is useful for importing existing family tree data or adding multiple members efficiently.

## How to Use

### 1. Navigate to Bulk Upload Page

- Log in to the Family Tree application
- Click the **"Add Members"** button in the top navigation bar (next to "Add Member")
- You will be taken to the bulk upload page

### 2. Prepare Your JSON File

Your JSON file must follow this structure:

```json
{
  "space_name": "Demo",
  "members": [
    {
      "first_name": "John",
      "last_name": "Doe",
      "dob": "01/15/1980",
      "nick_name": "Johnny",
      "middle_name": "Michael",
      "birth_location": "New York",
      "residence_location": "California",
      "email": "john@example.com",
      "phone": "555-1234",
      "hobbies": ["Reading", "Hiking"],
      "is_deceased": false,
      "date_of_death": null,
      "parent_name": "Jane Doe",
      "spouse_name": "Mary Doe"
    }
  ]
}
```

### Required Fields

- `space_name`: Name of the family space (must match an existing family space, case-insensitive)
- `members`: Array of member objects
  - `first_name`: First name (letters and hyphens only)
  - `last_name`: Last name (letters and hyphens only)
  - `dob`: Date of birth in MM/DD/YYYY format

### Optional Fields

For each member, you can include:
- `nick_name`: Nickname
- `middle_name`: Middle name
- `birth_location`: Place of birth
- `residence_location`: Current residence
- `email`: Email address
- `phone`: Phone number
- `hobbies`: Array of hobby strings
- `is_deceased`: Boolean indicating if deceased
- `date_of_death`: Date of death in MM/DD/YYYY format
- `parent_name`: Full name of parent (e.g., "Jane Doe") to establish parent-child relationship
- `spouse_name`: Full name of spouse (e.g., "Mary Doe") to establish spousal relationship

### 3. File Naming Convention

The JSON filename should contain the family space name. For example:
- `demo.json` for the "Demo" space
- `karunakaran.json` for the "Karunakaran" space
- `smith-family.json` for the "Smith" space

### 4. Upload Process

1. Click "Select JSON File" and choose your prepared JSON file
2. Review the file name and size confirmation
3. Click "Upload" button
4. Wait for the upload to complete

### 5. Review Results

After upload, you'll see:
- **Total members in file**: Total count in the JSON file
- **Successfully uploaded**: Number of new members added
- **Already present**: Number of members that already exist (skipped)
- **Errors**: Any errors encountered during upload

If all members were already present, you'll see a specific message indicating this.

## Features

### Title Case Conversion

All names (first, last, middle, nick, locations) are automatically converted to Title Case during upload, regardless of how they appear in the JSON file. For example:
- `"john doe"` becomes `"John Doe"`
- `"MARY SMITH"` becomes `"Mary Smith"`

### De-duplication

The system checks for existing members based on:
- First name (case-insensitive)
- Last name (case-insensitive)
- Date of birth (exact match)

If a member with the same first name, last name, and date of birth already exists in the family space, they are skipped and counted as "already present".

### Relationship Establishment

You can establish relationships in two ways:

1. **Parent-Child**: Use the `parent_name` field with the parent's full name
2. **Spouse**: Use the `spouse_name` field with the spouse's full name

Both relationships are established after all members are created, so you can reference members in the same upload file.

## Validation

The upload process validates:
1. JSON file format (must be valid JSON)
2. Family space name (must match an existing space)
3. Required fields presence
4. Date formats (MM/DD/YYYY)
5. Email format (if provided)
6. Name format (letters and hyphens only)

## Error Handling

If errors occur during upload:
- Each error is listed with the member index and details
- Already-uploaded members remain in the database
- You can fix the errors and re-upload (duplicates will be skipped)

## Security

- You must be logged in to access bulk upload
- You can only upload to your current family space
- Admin-level access may be required (depending on configuration)

## Example Files

A sample file `demo.json` is provided in the backend directory showing the correct format.

## Limitations

- Maximum file size: Depends on server configuration
- All members must be for the same family space
- Parent and spouse relationships can only reference members in the same upload or already existing in the database
- Names can only contain letters and hyphens

## Troubleshooting

### "Family space not found" error
- Verify the `space_name` in your JSON matches an existing family space exactly
- Check for typos in the space name

### "File name mismatch" error
- Ensure your filename contains the family space name
- Example: Use `demo.json` for the "Demo" space

### "Invalid JSON format" error
- Validate your JSON using a JSON validator tool
- Check for missing commas, brackets, or quotes
- Ensure all strings are in double quotes

### "Already present" for all members
- These members already exist in the database
- Check if you've already uploaded this file
- Verify you're uploading to the correct family space
