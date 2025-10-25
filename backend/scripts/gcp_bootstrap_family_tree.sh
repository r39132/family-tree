#!/usr/bin/env bash
set -euo pipefail

# === DEFAULT CONFIGURATION (can be overridden with arguments) ===
PROJECT_ID="${1:-family-tree-469815}"
REGION="${2:-us-central1}"
GAR_LOCATION="${3:-us-central1}"
DEPLOYER_SA_NAME="${4:-family-tree-deployer}"
RUNTIME_SA_NAME="${5:-family-tree-runtime}"
MAKE_DEPLOYER_KEY="${6:-true}"
KEY_OUTPUT_PATH="${HOME}/${DEPLOYER_SA_NAME}.json"
GCS_BUCKET_NAME="${PROJECT_ID}-profile-pictures"
ALBUM_BUCKET_NAME="${PROJECT_ID}-album-photos"

# Show usage if --help is provided
if [[ "${1:-}" == "--help" ]] || [[ "${1:-}" == "-h" ]]; then
  cat <<EOF
Usage: $0 [PROJECT_ID] [REGION] [GAR_LOCATION] [DEPLOYER_SA_NAME] [RUNTIME_SA_NAME] [MAKE_DEPLOYER_KEY]

GCP Bootstrap Script for Family Tree Application

This script sets up:
- Required GCP APIs (Cloud Run, Artifact Registry, Cloud Storage)
- Service accounts for deployment and runtime
- IAM bindings and permissions
- GCS bucket for profile pictures with private access (signed URLs)
- GCS bucket for family albums with private access (signed URLs + CDN support)
- Uniform bucket-level access for modern IAM

Arguments (all optional, defaults shown):
  PROJECT_ID           GCP project ID (default: family-tree-469815)
  REGION              Cloud Run region (default: us-central1)
  GAR_LOCATION        Artifact Registry location (default: us-central1)
  DEPLOYER_SA_NAME    Deployer service account name (default: family-tree-deployer)
  RUNTIME_SA_NAME     Runtime service account name (default: family-tree-runtime)
  MAKE_DEPLOYER_KEY   Generate deployer key: true/false (default: true)

Examples:
  # Use all defaults
  $0

  # Custom project ID only
  $0 my-project-id

  # Custom project and region
  $0 my-project-id us-west1

  # Full customization
  $0 my-project us-west1 us-west1 my-deployer my-runtime true

Environment:
  Requires: gcloud CLI, gsutil, jq
  Permissions: Project Owner or equivalent to create service accounts and set IAM policies

GCS Bucket:
  Profile pictures bucket: \${PROJECT_ID}-profile-pictures
  Family albums bucket: \${PROJECT_ID}-album-photos
  Location: Same as REGION parameter
  Access: Private (runtime SA has objectAdmin, uses signed URLs for secure access)

EOF
  exit 0
fi

# === DO NOT EDIT BELOW UNLESS YOU KNOW WHAT YOU'RE DOING ===
bold() { printf "\033[1m%s\033[0m\n" "$*"; }
note() { printf "🔹 %s\n" "$*"; }
ok()   { printf "✅ %s\n" "$*"; }
warn() { printf "⚠️  %s\n" "$*"; }

ensure_project() {
  gcloud config set project "$PROJECT_ID" >/dev/null
  gcloud projects describe "$PROJECT_ID" >/dev/null
  PROJECT_NUMBER="$(gcloud projects describe "$PROJECT_ID" --format='value(projectNumber)')"
  echo "$PROJECT_NUMBER"
}

enable_api() {
  local api="$1"
  if gcloud services list --enabled --format='value(config.name)' | grep -q "^${api}$"; then
    note "API already enabled: ${api}"
  else
    note "Enabling API: ${api}"
    gcloud services enable "$api"
  fi
}

ensure_sa() {
  local sa_name="$1"
  local sa_email="${sa_name}@${PROJECT_ID}.iam.gserviceaccount.com"
  if gcloud iam service-accounts list --format='value(email)' | grep -q "^${sa_email}$"; then
    note "Service account exists: ${sa_email}"
  else
    note "Creating service account: ${sa_email}"
    gcloud iam service-accounts create "$sa_name" \
      --display-name "$sa_name"
  fi
  echo "$sa_email"
}

has_binding() {
  local member="$1" role="$2"
  gcloud projects get-iam-policy "$PROJECT_ID" \
    --format=json | jq -e --arg m "$member" --arg r "$role" \
    '.bindings[]? | select(.role==$r) | .members[]? | select(.==$m)' >/dev/null 2>&1
}

bind_role() {
  local member="$1" role="$2"
  if has_binding "$member" "$role"; then
    note "IAM binding already present: $member -> $role"
  else
    note "Adding IAM binding: $member -> $role"
    gcloud projects add-iam-policy-binding "$PROJECT_ID" \
      --member "$member" \
      --role "$role" >/dev/null
  fi
}

bind_sa_user_on_sa() {
  local target_sa_email="$1" member_sa_email="$2"
  local member="serviceAccount:${member_sa_email}"
  local role="roles/iam.serviceAccountUser"
  if gcloud iam service-accounts get-iam-policy "$target_sa_email" --format=json \
     | jq -e --arg m "$member" --arg r "$role" \
        '.bindings[]? | select(.role==$r) | .members[]? | select(.==$m)' >/dev/null 2>&1
  then
    note "SA policy already has $member as $role on $target_sa_email"
  else
    note "Granting $role to $member on $target_sa_email"
    gcloud iam service-accounts add-iam-policy-binding "$target_sa_email" \
      --member "$member" \
      --role "$role" >/dev/null
  fi
}

maybe_make_key() {
  local sa_email="$1"
  local out="$2"
  if [[ "${MAKE_DEPLOYER_KEY}" == "true" ]]; then
    note "Creating a new JSON key for $sa_email → $out"
    gcloud iam service-accounts keys create "$out" --iam-account "$sa_email" >/dev/null
    ok "Key saved to $out"
    note "Base64 (for GitHub secret GCP_SA_KEY):"
    base64 "$out"
  else
    warn "Skipping key creation (MAKE_DEPLOYER_KEY=${MAKE_DEPLOYER_KEY})"
  fi
}

main() {
  bold "GCP bootstrap for Family Tree (project: ${PROJECT_ID})"

  # 0) Sanity: ensure jq exists
  command -v jq >/dev/null || { echo "Please install 'jq' (e.g., brew install jq)"; exit 1; }

  # 1) Project and APIs
  PROJECT_NUMBER="$(ensure_project)"
  ok "Using project ${PROJECT_ID} (${PROJECT_NUMBER})"

  # Service Usage must be first
  enable_api serviceusage.googleapis.com
  enable_api run.googleapis.com
  enable_api artifactregistry.googleapis.com
  enable_api storage.googleapis.com
  ok "Required APIs enabled"

  # 2) Service Accounts
  DEPLOYER_SA_EMAIL="$(ensure_sa "${DEPLOYER_SA_NAME}")"
  RUNTIME_SA_EMAIL="$(ensure_sa "${RUNTIME_SA_NAME}")"
  ok "Service accounts ready:
  - Deployer: ${DEPLOYER_SA_EMAIL}
  - Runtime : ${RUNTIME_SA_EMAIL}
  "

  # 3) IAM for Deployer (project-level)
  bind_role "serviceAccount:${DEPLOYER_SA_EMAIL}" "roles/run.admin"
  bind_role "serviceAccount:${DEPLOYER_SA_EMAIL}" "roles/artifactregistry.admin"
  # Deployer needs to be able to set the runtime SA on deploy
  bind_sa_user_on_sa "${RUNTIME_SA_EMAIL}" "${DEPLOYER_SA_EMAIL}"

  # 4) IAM for Runtime (pull images at runtime)
  bind_role "serviceAccount:${RUNTIME_SA_EMAIL}" "roles/artifactregistry.reader"

  ok "IAM bindings applied"

  # 5) Create GCS bucket for profile pictures
  note "Setting up GCS bucket for profile pictures: ${GCS_BUCKET_NAME}"

  # Check if bucket exists
  if gsutil ls -b "gs://${GCS_BUCKET_NAME}" >/dev/null 2>&1; then
    note "Bucket already exists: gs://${GCS_BUCKET_NAME}"
  else
    note "Creating bucket: gs://${GCS_BUCKET_NAME}"
    gsutil mb -p "${PROJECT_ID}" -l "${REGION}" "gs://${GCS_BUCKET_NAME}"
    ok "Bucket created: gs://${GCS_BUCKET_NAME}"
  fi

  # Enable uniform bucket-level access (modern IAM approach)
  note "Enabling uniform bucket-level access"
  gsutil uniformbucketlevelaccess set on "gs://${GCS_BUCKET_NAME}" 2>/dev/null || true

  # Grant runtime service account storage permissions
  note "Granting runtime SA storage permissions"
  gsutil iam ch "serviceAccount:${RUNTIME_SA_EMAIL}:objectAdmin" "gs://${GCS_BUCKET_NAME}"

  # Grant service usage permissions to runtime SA (required for quota checks)
  bind_role "serviceAccount:${RUNTIME_SA_EMAIL}" "roles/serviceusage.serviceUsageConsumer"

  ok "GCS bucket configured for profile pictures (private access only)"

  # 6) Create GCS bucket for family albums
  note "Setting up GCS bucket for family albums: ${ALBUM_BUCKET_NAME}"

  # Check if bucket exists
  if gsutil ls -b "gs://${ALBUM_BUCKET_NAME}" >/dev/null 2>&1; then
    note "Bucket already exists: gs://${ALBUM_BUCKET_NAME}"
  else
    note "Creating bucket: gs://${ALBUM_BUCKET_NAME}"
    gsutil mb -p "${PROJECT_ID}" -l "${REGION}" "gs://${ALBUM_BUCKET_NAME}"
    ok "Bucket created: gs://${ALBUM_BUCKET_NAME}"
  fi

  # Enable uniform bucket-level access
  note "Enabling uniform bucket-level access for album bucket"
  gsutil uniformbucketlevelaccess set on "gs://${ALBUM_BUCKET_NAME}" 2>/dev/null || true

  # Grant runtime service account storage permissions
  note "Granting runtime SA storage permissions for album bucket"
  gsutil iam ch "serviceAccount:${RUNTIME_SA_EMAIL}:objectAdmin" "gs://${ALBUM_BUCKET_NAME}"

  ok "GCS bucket configured for family albums (private access only)"

  # 7) (Optional) Create deployer key for GitHub Actions
  maybe_make_key "$DEPLOYER_SA_EMAIL" "$KEY_OUTPUT_PATH"

  bold "Done."
  echo
  bold "Next steps:"
  cat <<EOF
1) In GitHub → Settings → Secrets and variables → Actions:
   - Create secret  GCP_SA_KEY              ← paste the base64 from above (or upload ${KEY_OUTPUT_PATH} contents)
   - Create secret  GCP_PROJECT_ID          = ${PROJECT_ID}
   - Create secret  CLOUD_RUN_REGION        = ${REGION}
   - Create secret  GAR_LOCATION            = ${GAR_LOCATION}
   - Create secret  CLOUD_RUN_SERVICE       = family-tree-api
   - (Optional) CLOUD_RUN_RUNTIME_SA        = ${RUNTIME_SA_EMAIL}

2) Update your .env file with the GCS bucket names:
   GCS_BUCKET_NAME=${GCS_BUCKET_NAME}
   ALBUM_BUCKET_NAME=${ALBUM_BUCKET_NAME}
   MAX_UPLOAD_SIZE_MB=5
   ALBUM_MAX_UPLOAD_SIZE_MB=5

3) In your deploy step, specify the runtime SA and GCS buckets:
   gcloud run deploy \${{ secrets.CLOUD_RUN_SERVICE }} \\
     --image "\$IMAGE" \\
     --region \${{ secrets.CLOUD_RUN_REGION }} \\
     --platform managed \\
     --service-account ${RUNTIME_SA_EMAIL} \\
     --allow-unauthenticated \\
     --set-env-vars "GOOGLE_CLOUD_PROJECT=\${{ secrets.GCP_PROJECT_ID }}" \\
     --set-env-vars "FIRESTORE_DATABASE=family-tree" \\
     --set-env-vars "GCS_BUCKET_NAME=${GCS_BUCKET_NAME}" \\
     --set-env-vars "ALBUM_BUCKET_NAME=${ALBUM_BUCKET_NAME}" \\
     --set-env-vars "MAX_UPLOAD_SIZE_MB=5" \\
     --set-env-vars "ALBUM_MAX_UPLOAD_SIZE_MB=5"

3) If you prefer uploading the key with GitHub CLI:
   base64 -w0 "${KEY_OUTPUT_PATH}" | gh secret set GCP_SA_KEY
   gh secret set GCP_PROJECT_ID -b '${PROJECT_ID}'
   gh secret set CLOUD_RUN_REGION -b '${REGION}'
   gh secret set GAR_LOCATION -b '${GAR_LOCATION}'
   gh secret set CLOUD_RUN_SERVICE -b 'family-tree-api'
   gh secret set CLOUD_RUN_RUNTIME_SA -b '${RUNTIME_SA_EMAIL}'
EOF
}

main "$@"
