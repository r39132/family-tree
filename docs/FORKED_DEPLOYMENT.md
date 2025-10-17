# 🚀 Setting Up a Forked Deployment

This guide walks you through deploying your own instance of the Family Tree application after forking the repository.

## Prerequisites

Before you begin, ensure you have:

- Node 18+ and npm
- Python 3.12.3
- `uv` package manager ([install guide](https://docs.astral.sh/uv/))
- Google Cloud Platform account
- GitHub account (for CI/CD)
- `gcloud` CLI installed ([install guide](https://cloud.google.com/sdk/docs/install))
- `jq` command-line JSON processor (`brew install jq` on macOS)

## Step 1: Fork and Clone

Fork the repository on GitHub, then clone your fork:

```bash
git clone https://github.com/YOUR-USERNAME/family-tree.git
cd family-tree
```

## Step 2: Configure Your Environment

Create your configuration files with your own values:

### Backend Configuration

Create `backend/.env`:

```bash
GOOGLE_CLOUD_PROJECT=your-project-id
FIRESTORE_DATABASE=your-database-name
JWT_SECRET=your-unique-secret-key-min-32-chars

# Cloud Storage for profile pictures
GCS_BUCKET_NAME=your-project-id-profile-pictures
MAX_UPLOAD_SIZE_MB=5  # Optional, defaults to 5MB

# Optional: Google Maps integration
ENABLE_MAP=true
GOOGLE_MAPS_API_KEY=your-maps-api-key

# Optional: Email notifications
ENABLE_EMAIL=true
GMAIL_CREDENTIALS_JSON=path/to/credentials.json
GMAIL_TOKEN_JSON=path/to/token.json
```

**Security Notes:**
- Generate a strong `JWT_SECRET` (32+ characters)
- Never commit `.env` files to git (already in `.gitignore`)
- Keep API keys and credentials secure

### Frontend Configuration

Create `frontend/.env.local`:

```bash
# For local development
NEXT_PUBLIC_API_BASE=http://localhost:8080

# For production (update after deployment)
# NEXT_PUBLIC_API_BASE=https://your-api-url.run.app
```

## Step 3: Set Up GCP Infrastructure

Bootstrap your Google Cloud Platform project:

```bash
cd backend/scripts

# Option 1: Use defaults (recommended for first-time setup)
./gcp_bootstrap_family_tree.sh

# Option 2: Customize for your project
./gcp_bootstrap_family_tree.sh \
  your-project-id \
  us-west1 \
  us-west1 \
  your-deployer-sa \
  your-runtime-sa \
  true

# Show all available options
./gcp_bootstrap_family_tree.sh --help
```

### What This Script Does

The bootstrap script will:
- ✅ Enable required GCP APIs (Cloud Run, Artifact Registry)
- ✅ Create service accounts for deployment and runtime
- ✅ Set up IAM permissions
- ✅ Generate deployment keys for GitHub Actions
- ✅ Provide instructions for GitHub secrets setup

### Script Arguments

| Argument | Description | Default |
|----------|-------------|---------|
| PROJECT_ID | Your GCP project ID | `family-tree-469815` |
| REGION | Cloud Run deployment region | `us-central1` |
| GAR_LOCATION | Artifact Registry location | `us-central1` |
| DEPLOYER_SA_NAME | Deployer service account name | `family-tree-deployer` |
| RUNTIME_SA_NAME | Runtime service account name | `family-tree-runtime` |
| MAKE_DEPLOYER_KEY | Generate key (true/false) | `true` |

### Output

The script will output:
- Base64-encoded deployment key (for GitHub secret)
- Service account emails
- Instructions for GitHub secrets configuration

**Save this output!** You'll need it for Step 7.

### Create Cloud Storage Bucket (for Profile Pictures)

```bash
# Create a GCS bucket for storing profile pictures
gsutil mb -p your-project-id -l us-central1 gs://your-project-id-profile-pictures

# Make bucket publicly readable (required for displaying images)
gsutil iam ch allUsers:objectViewer gs://your-project-id-profile-pictures

# Enable uniform bucket-level access (recommended)
gsutil uniformbucketlevelaccess set on gs://your-project-id-profile-pictures
```

**Recommended bucket name:** `{your-project-id}-profile-pictures`
**Example:** `family-tree-469815-profile-pictures`

**Note:** This bucket name should match the `GCS_BUCKET_NAME` value in your `backend/.env` file.

## Step 4: Initialize Firestore Database

Create all required Firestore collections:

```bash
cd backend

# Initialize collections with placeholder documents
uv run python scripts/initialize_collections.py

# Optionally clean up placeholder documents later
uv run python scripts/initialize_collections.py --cleanup
```

### Collections Created

This script creates 7 essential collections:
- `users` - User authentication data
- `members` - Family tree member data
- `relations` - Parent-child relationships
- `member_keys` - Deleted member tracking
- `tree_versions` - Saved tree snapshots
- `tree_state` - Active version tracking
- `invites` - User invitation system

## Step 5: Create Your Admin Account

Create an admin user account with your own credentials:

```bash
# Create admin account with your credentials
uv run python scripts/seed_admin.py \
  --username yourusername \
  --email your@email.com \
  --password YourSecurePassword123

# Or use defaults (remember to change the password after first login!)
uv run python scripts/seed_admin.py
```

### Script Arguments

| Argument | Description | Default |
|----------|-------------|---------|
| `--username` | Admin username | `sanand` |
| `--email` | Admin email address | `sanand@apache.org` |
| `--password` | Admin password | `ChangeMe!123` |

**Important:** If using defaults, change the password after your first login!

## Step 6: (Optional) Add Test Data

For development and testing, you can populate the database with sample data:

```bash
# Create test data with default test user
uv run python scripts/populate_dummy_data.py

# Or customize the test user credentials
uv run python scripts/populate_dummy_data.py \
  --user-id my_test_user \
  --email test@mycompany.com \
  --password testpass123

# Clean up test data when done
uv run python scripts/populate_dummy_data.py \
  --cleanup \
  --user-id my_test_user
```

### Script Arguments

| Argument | Description | Default |
|----------|-------------|---------|
| `--user-id` | Test user username | `test_user_123` |
| `--email` | Test user email | `test@familytree.com` |
| `--password` | Test user password | `testpassword123` |
| `--cleanup` | Remove test data | `false` |

### Test Data Included

The dummy data creates:
- 9 family members across 3 generations
- Grandparents, children, and grandchildren
- Marriage relationships
- Rich member data (DOB, locations, hobbies, contact info)

This is useful for:
- Testing the application features
- Demos and presentations
- Development without entering real data

## Step 7: Configure GitHub Secrets

Set up GitHub secrets for CI/CD using values from Step 3:

### Using GitHub CLI (Recommended)

```bash
# Set the deployment key
gh secret set GCP_SA_KEY < ~/family-tree-deployer.json

# Set project configuration
gh secret set GCP_PROJECT_ID -b 'your-project-id'
gh secret set CLOUD_RUN_REGION -b 'us-central1'
gh secret set GAR_LOCATION -b 'us-central1'
gh secret set CLOUD_RUN_SERVICE -b 'family-tree-api'
gh secret set CLOUD_RUN_RUNTIME_SA -b 'your-runtime-sa@your-project-id.iam.gserviceaccount.com'
```

### Manual Setup in GitHub UI

1. Go to your repository on GitHub
2. Navigate to: **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret**
4. Add each secret:

| Secret Name | Value | Source |
|-------------|-------|--------|
| `GCP_SA_KEY` | Base64 deployment key | From Step 3 output |
| `GCP_PROJECT_ID` | Your GCP project ID | Your project |
| `CLOUD_RUN_REGION` | Deployment region | From Step 3 |
| `GAR_LOCATION` | Artifact Registry location | From Step 3 |
| `CLOUD_RUN_SERVICE` | `family-tree-api` | Service name |
| `CLOUD_RUN_RUNTIME_SA` | Runtime SA email | From Step 3 output |

## Step 8: Deploy!

Push your changes to trigger automated deployment:

```bash
# Review your changes
git status

# Add configuration files (except .env files which are gitignored)
git add .

# Commit your changes
git commit -m "Configure for my deployment"

# Push to trigger CI/CD
git push origin main
```

### What Happens Next

GitHub Actions will automatically:
1. 🏗️ **Build** Docker images for frontend and backend
2. 📦 **Push** images to Google Artifact Registry
3. 🚀 **Deploy** to Google Cloud Run
4. ✅ **Run** health checks to verify deployment

### Monitor Deployment

Watch the deployment progress:
- Go to your repository on GitHub
- Click on **Actions** tab
- Select the latest workflow run
- Monitor each step's progress

### Access Your Application

Once deployed, Cloud Run will provide a URL like:
```
https://family-tree-api-XXXXX-uc.a.run.app
```

Update your `frontend/.env.local` with this URL and redeploy if needed.

## Quick Reference

### Required Scripts

| Script | Purpose | When to Run |
|--------|---------|-------------|
| `gcp_bootstrap_family_tree.sh` | Set up GCP infrastructure | Once, before deployment |
| `initialize_collections.py` | Create Firestore collections | Once, after GCP setup |
| `seed_admin.py` | Create admin account | Once, after collections |

### Optional Scripts

| Script | Purpose | When to Run |
|--------|---------|-------------|
| `populate_dummy_data.py` | Add test/demo data | For development/testing |
| `create_user_account.py` | Create additional users | As needed |

### Command Summary

```bash
# Complete setup in order
cd family-tree
./backend/scripts/gcp_bootstrap_family_tree.sh your-project-id
cd backend
uv run python scripts/initialize_collections.py
uv run python scripts/seed_admin.py --username you --email you@email.com --password YourPass123
uv run python scripts/populate_dummy_data.py  # Optional
cd ..
git add .
git commit -m "Configure for deployment"
git push origin main
```

## Troubleshooting

### "Permission denied" on shell scripts

**Problem:** Shell script cannot execute
**Solution:**
```bash
chmod +x backend/scripts/*.sh
```

### "Collection already exists"

**Problem:** Script says collection exists
**Solution:** This is normal - scripts are idempotent and safe to re-run.

### "Could not find test user" when using `create_user_account.py`

**Problem:** Script can't find test user to transfer data
**Solution:** Either:
- Run `populate_dummy_data.py` first, or
- Use `--no-transfer` flag to create user without data

### "gcloud: command not found"

**Problem:** gcloud CLI not installed
**Solution:** Install from https://cloud.google.com/sdk/docs/install

### "jq: command not found"

**Problem:** jq not installed
**Solution:** Install with `brew install jq` (macOS) or your package manager

### Firestore connection errors

**Problem:** Can't connect to Firestore
**Solution:** Ensure these environment variables are set in `backend/.env`:
- `GOOGLE_CLOUD_PROJECT`
- `FIRESTORE_DATABASE`
- `GCS_BUCKET_NAME` (optional, for profile picture uploads)
- `MAX_UPLOAD_SIZE_MB` (optional, defaults to 5MB)

And authenticate with: `gcloud auth application-default login`

### GitHub Actions deployment fails

**Problem:** CI/CD pipeline fails
**Solution:** Check that all GitHub secrets are set correctly:
```bash
# List your secrets (doesn't show values, just names)
gh secret list
```

### Cloud Run deployment succeeds but app doesn't work

**Problem:** App deployed but returns errors
**Solution:** Check Cloud Run logs:
```bash
gcloud run services logs read family-tree-api \
  --project your-project-id \
  --region us-central1
```

## Next Steps

After successful deployment:

1. **Update Frontend Config:** Update `NEXT_PUBLIC_API_BASE` in `frontend/.env.local` with your Cloud Run URL
2. **Test Your App:** Access your Cloud Run URL and test all features
3. **Customize:** Modify the application to fit your needs
4. **Add Users:** Use `create_user_account.py` to add more users
5. **Monitor:** Set up Cloud Monitoring alerts for your services
6. **Secure:** Review and tighten IAM permissions as needed

## Additional Resources

- [Architecture Documentation](ARCHITECTURE.md) - System design and data flow
- [Backend Scripts Documentation](BACKEND_SCRIPTS.md) - Detailed script reference
- [Deployment Guide](DEPLOYMENT.md) - Advanced deployment topics
- [Contributing Guide](CONTRIBUTING.md) - Development workflow and standards

## Support

If you encounter issues:

1. Check this troubleshooting section
2. Review script documentation in [BACKEND_SCRIPTS.md](BACKEND_SCRIPTS.md)
3. Check the [GitHub Issues](https://github.com/r39132/family-tree/issues) for similar problems
4. Create a new issue with:
   - Clear description of the problem
   - Steps to reproduce
   - Error messages and logs
   - Your environment (OS, versions, etc.)

---

**Last Updated:** October 16, 2025
