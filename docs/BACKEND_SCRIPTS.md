# Backend Scripts Documentation

Comprehensive documentation for utility scripts in `backend/scripts/`. These scripts handle development, testing, and deployment tasks.

**Last Updated:** October 17, 2025

---

## Quick Reference

| Script | Category | Purpose | When to Use |
|--------|----------|---------|-------------|
| `gcp_bootstrap_family_tree.sh` | 🚀 Deploy | Set up GCP infrastructure | ✅ Required for production |
| `initialize_collections.py` | 📦 Setup | Create Firestore collections | ✅ Required (first setup) |
| `seed_admin.py` | 👤 Setup | Create admin account | ✅ Required |
| `populate_dummy_data.py` | 🧪 Testing | Create test family tree data | ⚠️ Optional (development) |
| `seed_demo_album.py` | 🧪 Testing | Seed album with test photos | ⚠️ Optional (development) |
| `import_whatsapp_photos.py` | 📸 Utility | Import WhatsApp photos to album | ⚠️ Optional (production) |
| `create_user_account.py` | 👥 Utility | Create user accounts | ⚠️ Optional (multi-user) |

---

## Table of Contents

1. [Quick Start](#quick-start) - Essential setup for new deployments
2. [Setup Scripts](#setup-scripts) - Required initialization scripts
3. [Testing & Development](#testing--development) - Optional test data scripts
4. [Utility Scripts](#utility-scripts) - Account and database management
5. [Deployment Scripts](#deployment-scripts) - GCP infrastructure automation
6. [Workflow Examples](#workflow-examples) - Common usage patterns
7. [Troubleshooting](#troubleshooting) - Common issues and solutions

---

## Quick Start

**For new deployments, run these scripts in order:**

```bash
# 1. Set up GCP infrastructure (production only)
./backend/scripts/gcp_bootstrap_family_tree.sh your-project-id

# 2. Initialize database collections
cd backend
uv run python scripts/initialize_collections.py

# 3. Create your admin account
uv run python scripts/seed_admin.py \
  --username admin \
  --email admin@yourcompany.com \
  --password SecurePass123

# 4. (Optional) Add test data for development
uv run python scripts/populate_dummy_data.py
```

---

## Setup Scripts

Essential scripts for initializing a new deployment.

---

### `initialize_collections.py`

**Category:** Setup
**Required:** ✅ Yes (first-time setup)

**Purpose:** Creates all required Firestore collections with placeholder documents.

**Usage:**
```bash
# Initialize collections
uv run python scripts/initialize_collections.py

# Initialize and cleanup placeholders
uv run python scripts/initialize_collections.py --cleanup
```

**What it does:**
1. Creates 7 essential Firestore collections:
   - `users`: User authentication data
   - `members`: Family tree member data
   - `relations`: Parent-child relationships
   - `member_keys`: Deleted member tracking (unique name constraint)
   - `tree_versions`: Saved tree snapshots
   - `tree_state`: Active version tracking per user
   - `invites`: User invitation system
2. Each collection gets a `_placeholder` document to ensure it exists
3. Optional cleanup removes placeholder documents

**Parameters:**
- `--cleanup`: Remove placeholder documents after initialization

**Safety Notes:**
- ✅ Safe to run multiple times (idempotent)
- ✅ Creates collections if they don't exist
- ✅ Placeholder documents marked with `is_placeholder: true`
- Placeholders are automatically ignored by application logic

**Use Cases:**
- First-time database setup
- Recreating collections after reset
- Ensuring all required collections exist

---

### `seed_admin.py`

**Category:** Setup
**Required:** ✅ Yes

**Purpose:** Creates or promotes a user account with admin privileges.

**Usage:**
```bash
# Create admin with default credentials
uv run python scripts/seed_admin.py

# Create admin with custom credentials
uv run python scripts/seed_admin.py \
  --username myadmin \
  --email admin@mycompany.com \
  --password SecureAdminPass123
```

**Arguments:**
- `--username` - Username for admin account (default: `sanand`)
- `--email` - Email address (default: `sanand@apache.org`)
- `--password` - Account password (default: `ChangeMe!123`)

**What it does:**
1. Creates user account with specified credentials
2. Sets temporary/specified password
3. Grants admin role to the user
4. Updates tree state and admin metadata

**Safety Notes:**
- ⚠️ Change default password immediately after first login
- Safe to run multiple times (updates existing account if present)
- Creates necessary Firestore collections if they don't exist

**Dependencies:**
- `app.firestore_client.get_db()`
- `app.auth_utils.hash_password()`

**Output:**
- Admin user account ready for login
- Admin role assigned in database

---

## Testing & Development

Optional scripts for creating test data and development environments.

---

### `populate_dummy_data.py`

**Category:** Testing
**Required:** ⚠️ Optional (development/testing only)

**Purpose:** Creates comprehensive test data with a multi-generation family tree for testing and development.

**Usage:**
```bash
# Create dummy data with defaults
uv run python scripts/populate_dummy_data.py

# Create with custom test user
uv run python scripts/populate_dummy_data.py \
  --user-id my_test_user \
  --email test@mycompany.com \
  --password testpass123

# Remove dummy data
uv run python scripts/populate_dummy_data.py --cleanup --user-id my_test_user
```

**Arguments:**
- `--cleanup` - Remove dummy data instead of creating it
- `--user-id` - Username/ID for test user (default: `test_user_123`)
- `--email` - Email address (default: `test@familytree.com`)
- `--password` - Password (default: `testpassword123`)

**What it does:**
1. Creates test user with specified credentials
2. Populates 3-generation family tree:
   - **Grandparents:** Robert "Bob" Johnson (deceased), Margaret "Maggie" Johnson
   - **Children:** Michael Johnson (married to Sarah), Jennifer Smith
   - **Grandchildren:** Emily, Daniel (from Michael/Sarah); Ashley, Tyler (from Jennifer)
3. Creates 10 family relationships (parent-child links)
4. Initializes tree state for the test user

**Safety Notes:**
- ⚠️ Creates 9 members and associated data
- ✅ Can be cleaned up with `--cleanup` flag
- ✅ All data scoped to specified user_id for easy cleanup
- Includes rich test data: hobbies, spouse relationships, contact info, locations

**Dependencies:**
- `app.firestore_client.get_db()`
- `app.auth_utils.hash_password()`

**Default Test User Credentials:**
- Username: `test_user_123`
- Email: `test@familytree.com`
- Password: `testpassword123`

**Family Structure:**
```
Grandparents:
├─ Robert 'Bob' Johnson (03/15/1935) ⚰️
└─ Margaret 'Maggie' Johnson (07/08/1938)

Their Children:
├─ Michael Johnson (09/12/1965) 💑 Sarah Johnson (04/20/1967)
└─ Jennifer Smith (12/03/1968)

Grandchildren:
├─ From Michael & Sarah:
│  ├─ Emily Johnson (06/18/1995)
│  └─ Daniel Johnson (01/25/1998)
└─ From Jennifer:
   ├─ Ashley Smith (10/14/1992)
   └─ Tyler Smith (03/07/1996)
```

---

### `seed_demo_album.py`

**Category:** Testing
**Required:** ⚠️ Optional (development/testing only)

**Purpose:** Seeds the album with test photos for development and testing.

**Usage:**
```bash
# Seed album with test photos
uv run python scripts/seed_demo_album.py --space-id karunakaran
```

**What it does:**
1. Downloads sample photos from placeholder image services
2. Uploads them to the specified space's album
3. Creates test photo entries with sample captions and metadata

**Safety Notes:**
- ⚠️ Downloads external images from the internet
- ✅ For development/testing purposes only
- See `import_whatsapp_photos.py` for production WhatsApp photo imports

---

### `import_whatsapp_photos.py`

**Category:** Utility
**Required:** ⚠️ Optional (for importing real photos)

**Purpose:** Imports photos from WhatsApp chat exports into the Family Tree album.

**Usage:**
```bash
# Basic import
uv run python scripts/import_whatsapp_photos.py \
  --export-folder /path/to/whatsapp/export \
  --space-id karunakaran \
  --token YOUR_AUTH_TOKEN

# With phone number mapping
uv run python scripts/import_whatsapp_photos.py \
  --export-folder /path/to/whatsapp/export \
  --space-id karunakaran \
  --mapping-file phone_mapping.json \
  --token YOUR_AUTH_TOKEN

# Dry run to test without uploading
uv run python scripts/import_whatsapp_photos.py \
  --export-folder /path/to/whatsapp/export \
  --space-id karunakaran \
  --dry-run
```

**What it does:**
1. Parses WhatsApp chat export `_chat.txt` file
2. Extracts photo messages with metadata (date, time, sender, caption)
3. Matches photo filenames with actual files in export folder
4. Maps WhatsApp senders to Family Tree user IDs (if mapping provided)
5. Uploads photos in bulk using the album API endpoint
6. Preserves original captions and metadata

**Arguments:**
- `--export-folder` - Path to WhatsApp chat export folder (required)
- `--space-id` - Space ID to upload photos to (required)
- `--mapping-file` - JSON file mapping phone numbers to user IDs (optional)
- `--api-url` - Backend API base URL (default: `http://localhost:8000`)
- `--token` - Auth token (or use `AUTH_TOKEN` env var)
- `--dry-run` - Parse and prepare but don't upload

**Phone Mapping File:**
Create a JSON file mapping WhatsApp sender names/numbers to member IDs:
```json
{
  "Siddharth Anand": "orTx8ZIGCxDYnB81uXKS",
  "+919876543210": "member_id_relative1",
  "Mom": "member_id_mom"
}
```

**Safety Notes:**
- ✅ Designed for production use with real WhatsApp exports
- ✅ Dry-run mode for testing before actual upload
- ✅ Preserves original metadata from WhatsApp messages
- ⚠️ Requires valid authentication token
- ⚠️ Photos must meet backend size limits (default: 10MB)

**Dependencies:**
- `requests` - HTTP client for API calls
- `python-dotenv` - Environment variable management

**See Also:**
- Complete documentation: [WHATSAPP_IMPORT.md](WHATSAPP_IMPORT.md)
- Example phone mapping file: `scripts/phone_mapping.example.json`

---

## Utility Scripts

Scripts for ongoing database operations and account management.

---

### `create_user_account.py`

**Category:** Utility
**Required:** ⚠️ Optional (multi-user setups)

**Purpose:** Creates user accounts and optionally transfers dummy data to new users.

**Usage:**
```bash
# Create account with default values (sanand)
uv run python scripts/create_user_account.py

# Create custom account with data transfer
uv run python scripts/create_user_account.py --username johndoe --email john@example.com --password secure123

# Create account without transferring dummy data
uv run python scripts/create_user_account.py --username janedoe --email jane@example.com --password secure456 --no-transfer
```

**What it does:**
1. Creates new user account with hashed password
2. Initializes tree state for the user
3. Optionally transfers data from `test_user_123` to new user
4. Updates all member and relation documents to new user_id

**Parameters:**
- `--username`: Username for the account (default: `sanand`)
- `--email`: Email address (default: `sanand@apache.org`)
- `--password`: Account password (default: `pw`)
- `--no-transfer`: Skip transferring dummy data from test_user_123

**Safety Notes:**
- ⚠️ Updates existing user if username already exists
- ⚠️ Data transfer modifies all test_user_123 data
- ✅ Hashes passwords using bcrypt
- Creates proper authentication records

**Use Cases:**
- Setting up new user accounts for testing
- Transferring test data to real user accounts
- Rapid account creation for development

**Dependencies:**
- `app.firestore_client.get_db()`
- `app.auth_utils.hash_password()`

**Output:**
- New user account with credentials
- Optionally populated with family tree data from test user

---

## Deployment Scripts

Automation scripts for GCP infrastructure setup and deployment.

---

### `gcp_bootstrap_family_tree.sh`

**Category:** Deployment
**Required:** ✅ Yes (for production deployment)

**Purpose:** Automates GCP project setup for deploying Family Tree app to Cloud Run.

**Usage:**
```bash
# Use defaults
./gcp_bootstrap_family_tree.sh

# Custom project ID only
./gcp_bootstrap_family_tree.sh my-project-id

# Custom project and region
./gcp_bootstrap_family_tree.sh my-project-id us-west1

# Full customization
./gcp_bootstrap_family_tree.sh \
  my-project-id \
  us-west1 \
  us-west1 \
  my-deployer-sa \
  my-runtime-sa \
  true

# Show help
./gcp_bootstrap_family_tree.sh --help
```

**Arguments (all optional):**
1. `PROJECT_ID` - GCP project ID (default: `family-tree-469815`)
2. `REGION` - Cloud Run region (default: `us-central1`)
3. `GAR_LOCATION` - Artifact Registry location (default: `us-central1`)
4. `DEPLOYER_SA_NAME` - Deployer service account name (default: `family-tree-deployer`)
5. `RUNTIME_SA_NAME` - Runtime service account name (default: `family-tree-runtime`)
6. `MAKE_DEPLOYER_KEY` - Generate deployer key: `true`/`false` (default: `true`)

**What it does:**
1. **Configures GCP Project:**
   - Sets specified project ID or uses default
   - Configures region and Artifact Registry location

2. **Enables Required APIs:**
   - `serviceusage.googleapis.com`
   - `run.googleapis.com` (Cloud Run)
   - `artifactregistry.googleapis.com`

3. **Creates Service Accounts:**
   - **Deployer SA:** Used for CI/CD deployments (GitHub Actions)
     - Roles: `roles/run.admin`, `roles/artifactregistry.admin`
   - **Runtime SA:** Used by Cloud Run service at runtime
     - Roles: `roles/artifactregistry.reader`

4. **Sets IAM Permissions:**
   - Grants deployer SA permission to use runtime SA (`roles/iam.serviceAccountUser`)
   - Binds roles at project level

5. **Generates Deployment Key (Optional):**
   - Creates JSON key for deployer service account
   - Outputs base64-encoded key for GitHub secret `GCP_SA_KEY`
   - Saves key to `~/<deployer-sa-name>.json`

**Safety Notes:**
- ⚠️ Creates GCP resources (service accounts, IAM bindings)
- ⚠️ Generates service account keys (sensitive credentials)
- ✅ Idempotent - safe to run multiple times
- ✅ Checks existing resources before creating
- Requires `gcloud` CLI and `jq` installed
- Requires appropriate GCP permissions to create service accounts and bind IAM roles

**GitHub Secrets Setup:**

After running this script, configure these GitHub secrets:

```bash
# Option 1: Manual setup in GitHub UI
GCP_SA_KEY              # Base64 key from script output
GCP_PROJECT_ID          # Your project ID
CLOUD_RUN_REGION        # Your region
GAR_LOCATION            # Your GAR location
CLOUD_RUN_SERVICE       # family-tree-api
CLOUD_RUN_RUNTIME_SA    # Runtime SA email from script output

# Option 2: Using GitHub CLI
base64 -w0 ~/<deployer-sa-name>.json | gh secret set GCP_SA_KEY
gh secret set GCP_PROJECT_ID -b 'family-tree-469815'
gh secret set CLOUD_RUN_REGION -b 'us-central1'
gh secret set GAR_LOCATION -b 'us-central1'
gh secret set CLOUD_RUN_SERVICE -b 'family-tree-api'
gh secret set CLOUD_RUN_RUNTIME_SA -b 'family-tree-runtime@family-tree-469815.iam.gserviceaccount.com'
```

**Dependencies:**
- `gcloud` CLI (Google Cloud SDK)
- `jq` (JSON processor)
- Appropriate GCP project permissions

**Output:**
- Configured GCP project ready for Cloud Run deployment
- Service accounts with proper IAM roles
- Deployment key for CI/CD pipeline
- Step-by-step instructions for GitHub Actions setup

**Use Cases:**
- First-time GCP infrastructure setup
- Recreating service accounts after accidental deletion
- Setting up new deployment environments

---

## Workflow Examples

### Fresh Development Setup

```bash
# 1. Set up GCP (for production deployment)
cd backend/scripts
./gcp_bootstrap_family_tree.sh your-project-id us-west1

# 2. Initialize Firestore collections
cd backend
uv run python scripts/initialize_collections.py

# 3. Create your admin user
uv run python scripts/seed_admin.py \
  --username youradmin \
  --email admin@yourcompany.com \
  --password YourSecurePass123

# 4. (Optional) Populate test data
uv run python scripts/populate_dummy_data.py \
  --user-id test_user \
  --email test@yourcompany.com \
  --password testpass

# Now you have:
# - Admin user: youradmin / YourSecurePass123
# - Test user: test_user / testpass (optional)
# - Complete 3-generation Johnson family tree (optional)
```

### Testing with Custom User

```bash
# 1. Create test data with custom user
uv run python scripts/populate_dummy_data.py \
  --user-id demo_user \
  --email demo@example.com \
  --password demopass123

# 2. Create additional user account with test data transfer
uv run python scripts/create_user_account.py \
  --username alice \
  --email alice@example.com \
  --password alicepass

# 3. Test with your account
# Login with: alice / alicepass
# You'll have the full Johnson family tree transferred from demo_user
```

### GCP Deployment Setup

```bash
# 1. Run bootstrap script with your project details
cd backend/scripts
./gcp_bootstrap_family_tree.sh \
  my-family-tree-project \
  us-west1 \
  us-west1 \
  my-deployer \
  my-runtime \
  true

# 2. Copy the base64 key output

# 3. Configure GitHub secrets (see script output for instructions)
gh secret set GCP_SA_KEY < ~/my-deployer.json
gh secret set GCP_PROJECT_ID -b 'my-family-tree-project'
# ... etc

# 4. Push to GitHub - CI/CD will deploy to Cloud Run
```

---

## Troubleshooting

Common issues and their solutions.

### "Permission denied" on shell scripts
**Solution:** Make scripts executable:
```bash
chmod +x backend/scripts/*.sh
```

### "Collection already exists"
**Solution:** This is normal - scripts are idempotent and safe to re-run.

### "Could not find test user" when using `create_user_account.py`
**Solution:** Run `populate_dummy_data.py` first to create the test user, or use `--no-transfer` flag.



### "User already exists"
**Script:** `create_user_account.py` or `seed_admin.py`
**Solution:** This is expected behavior - the script will update the existing user's password.

### Script can't import app modules
**Solution:** Scripts use `sys.path.insert` to import from parent directory. Always run from the `backend/` directory using `uv run python scripts/script_name.py`.

### Firestore connection errors
**Solution:** Ensure environment variables are set:
- `GOOGLE_CLOUD_PROJECT`
- `FIRESTORE_DATABASE`
- Appropriate GCP authentication (service account key or `gcloud auth`)

---

## Development Guidelines

### Adding New Scripts

When creating new scripts, follow these guidelines:

1. **Location:** Place in `backend/scripts/`
2. **Shebang:** Use `#!/usr/bin/env python3` for Python scripts
3. **Imports:** Add path modification for app imports:
   ```python
   import sys
   import os
   sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
   ```
4. **Arguments:** Use `argparse` with sensible defaults - avoid hardcoding values
5. **Documentation:**
   - Add comprehensive docstring explaining purpose and usage
   - Include examples in docstring
   - Update this documentation file
6. **Safety:**
   - Add appropriate warnings for destructive operations
   - Make scripts idempotent when possible
   - Confirm before destructive actions
7. **Categories:**
   - **Setup:** Required initialization (keep)
   - **Testing:** Development/test data (keep)
   - **Utility:** Ongoing operations (keep)
   - **Deployment:** Infrastructure automation (keep)
   - **Migration:** One-time transformations (remove after use)
   - **Debug:** Temporary analysis (remove after issue resolved)

### Script Maintenance

**Keep scripts that are:**
- Reusable with different configurations
- Required for setup/deployment
- Useful for development/testing
- Well-documented with clear parameters

**Remove scripts that are:**
- One-time operations (migrations, fixes)
- Hardcoded with project-specific data
- Superseded by better alternatives
- No longer relevant to the project

---

## Additional Resources

- **Deployment Guide:** See [FORKED_DEPLOYMENT.md](FORKED_DEPLOYMENT.md) for complete setup walkthrough
- **Profile Pictures:** See [PROFILE_PICTURES.md](PROFILE_PICTURES.md) for GCS bucket setup
- **Project README:** See [README.md](../README.md) for general documentation
- **Git History:** Check git history for previous scripts and migrations

---

## Questions or Issues?

If you encounter issues with any script:
1. ✅ Check this documentation first
2. ✅ Review the script's source code and inline comments
3. ✅ Check the relevant guides (FORKED_DEPLOYMENT.md, etc.)
4. ✅ Search git history if referencing old functionality
5. ✅ Create a GitHub issue with detailed information

---

**Last Updated:** October 17, 2025
**Active Scripts:** 5 (2 setup, 1 testing, 1 utility, 1 deployment)
**Maintained by:** Project contributors
