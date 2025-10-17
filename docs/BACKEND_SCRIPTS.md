# Backend Scripts Documentation

This document provides comprehensive documentation for the utility scripts in `backend/scripts/`. These scripts are maintained for development, testing, and deployment purposes.

**Last Updated:** October 16, 2025

---

## Table of Contents

1. [Seed Scripts](#seed-scripts) - Initialize data for development/testing
2. [Utility Scripts](#utility-scripts) - Database operations and account management
3. [Deployment Scripts](#deployment-scripts) - GCP infrastructure setup
4. [For New Users](#for-new-users) - Setup guide for forked deployments

---

## Seed Scripts

These scripts populate the database with initial data for development and testing.

### `seed_admin.py`

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

### `populate_dummy_data.py`

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

## Utility Scripts

These scripts perform database operations and account management.

### `create_user_account.py`

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

### `initialize_collections.py`

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

**Dependencies:**
- `app.firestore_client.get_db()`

**Output:**
- All 7 required collections created and ready for use
- Placeholder documents can be cleaned up with `--cleanup`

---

## Deployment Scripts

These scripts handle GCP infrastructure setup and configuration.

### `gcp_bootstrap_family_tree.sh`

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

## For New Users

If you're forking this project to deploy your own Family Tree application, see the [README Quick Setup Guide](../README.md#-setting-up-a-forked-deployment) for a complete step-by-step walkthrough.

**TL;DR - Essential Scripts for Forked Deployment:**

| Script | Purpose | Required? |
|--------|---------|-----------|
| `gcp_bootstrap_family_tree.sh` | Set up GCP infrastructure | ✅ Yes (production) |
| `initialize_collections.py` | Create Firestore collections | ✅ Yes |
| `seed_admin.py` | Create admin account | ✅ Yes |
| `populate_dummy_data.py` | Add test/demo data | ⚠️ Optional |
| `create_user_account.py` | Create additional users | ⚠️ Optional |

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

## Removed Scripts

The following scripts have been removed as they were either one-time operations that have been executed, or too project-specific. They are preserved in git history if needed for reference:

### Migrations (7 scripts)
- `migrate_invites_active_to_status.py`
- `migrate_timezone_aware.py`
- `migrate_to_global_tree.py`
- `scripts_migrate_dob_format.py`
- `backfill_tree_versions.py`
- `scripts_backfill_dob_ts.py`
- `scripts_titlecase_members.py`

### Fixes (2 scripts)
- `fix_broken_tree.py`
- `fix_tree_structure.py`

### Cleanup (1 script)
- `cleanup_placeholders.py`

### Debug/Analysis (4 scripts)
- `analyze_tree_structure.py`
- `check_data_format.py`
- `debug_member_count.py`
- `debug_tree_logic.py`

### Project-Specific (3 scripts) - Removed October 16, 2025
- `scripts_seed_roots.py` - Hardcoded root members ("Achan", "Nanan")
- `add_marriage.py` - Hardcoded marriage (Robert & Margaret Johnson)
- `reset_database.py` - Dangerous script (deletes all data)

**Note:** These removed scripts can be found in git history prior to their removal dates.

---

## Common Issues & Solutions

### "Permission denied" on shell scripts
**Solution:** Make scripts executable:
```bash
chmod +x backend/scripts/*.sh
```

### "Collection already exists"
**Solution:** This is normal - scripts are idempotent and safe to re-run.

### "Could not find test user" when using `create_user_account.py`
**Solution:** Run `populate_dummy_data.py` first to create the test user, or use `--no-transfer` flag.

### "Could not find Robert and Margaret Johnson"
**Cause:** This refers to a removed script (`add_marriage.py`)
**Solution:** The marriage relationship is now automatically created by `populate_dummy_data.py`.

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

1. **Location:** Place in `backend/scripts/`
2. **Arguments:** Use `argparse` with sensible defaults for configurability
3. **Imports:** Add path modification for app imports:
   ```python
   import sys
   import os
   sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
   ```
3. **Shebang:** Use `#!/usr/bin/env python3` for executability
4. **Arguments:** Use `argparse` with sensible defaults - avoid hardcoding values
5. **Documentation:** Add docstring explaining purpose and usage
6. **Safety:** Add appropriate warnings for destructive operations
7. **Idempotency:** Make scripts safe to run multiple times when possible
8. **Update this doc:** Add entry in appropriate section

### Script Categories

- **Seed:** Initialize/populate data for testing (reusable, with configurable parameters)
- **Utility:** Database operations, account management (reusable)
- **Deployment:** Infrastructure setup (reusable with arguments)
- **Migration:** One-time data transformations (remove after execution)
- **Fix:** One-time repairs (remove after execution)
- **Debug:** Analysis tools (remove after issue resolved)
- **Project-Specific:** Hardcoded for specific data (remove before open-sourcing)

### Cleanup Policy

Scripts that should be removed:
1. One-time operations (migrations, fixes) - after execution and verification
2. Project-specific scripts with hardcoded personal data
3. Dangerous scripts (like `reset_database.py`) unless needed for development

When removing:
1. Document in git history
2. List in "Removed Scripts" section with reason
3. Note date of removal

---

## Questions or Issues?

If you encounter issues with any script or need to add new functionality:
1. Check this documentation first
2. Review the script's source code and comments
3. Check git history for removed scripts if needed
4. See the [README Setup Guide](../README.md#-setting-up-a-forked-deployment) for deployment instructions
5. Create a GitHub issue with details

---

**Last Updated:** October 16, 2025
**Scripts Documented:** 5 (1 seed, 2 utility, 1 deployment, 1 optional test data)
**Removed Scripts:** 17 (14 one-time operations + 3 project-specific, preserved in git history)
