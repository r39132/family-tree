# 🌳 Family Tree

![Python](https://img.shields.io/badge/Python-3.12.3-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.112%2B-009485)
![Next.js](https://img.shields.io/badge/Next.js-14-black)
![Node](https://img.shields.io/badge/Node-20.x-339933)
![Ruff](https://img.shields.io/badge/Lint-ruff-46a7f8)
![Black](https://img.shields.io/badge/Format-black-000000)
![pytest](https://img.shields.io/badge/tests-pytest-0A9EDC)
[![License](https://img.shields.io/badge/License-AGPLv3-blue)](LICENSE)
![Coverage](docs/coverage.svg)

[![CI-CD](https://github.com/r39132/family-tree/actions/workflows/ci-cd.yml/badge.svg)](https://github.com/r39132/family-tree/actions/workflows/ci-cd.yml)

A full‑stack **Family Tree** application with modern web technologies, designed for local development and cloud deployment.

**Tech Stack:**
- **Frontend:** Next.js (TypeScript) with ESLint and nature‑themed UI
- **Backend:** FastAPI (Python 3.12.3) with JWT authentication
- **Database:** Google Firestore
- **Development:** Pre-commit hooks, syntax validation, automated testing
- **Deployment:** Docker + GitHub Actions CI/CD to Google Cloud Run

## Features

- **Authentication:** Login, register with invite codes, password reset
- **Family Tree:** Visual tree with CRUD operations, member relationships
- **Profile Pictures:** Upload and manage member profile pictures with automatic optimization
- **Bulk Upload:** Import multiple family members from JSON files with automatic de-duplication
- **Map Integration:** Optional Google Maps integration for member locations
- **Quality Assurance:** Comprehensive testing, linting, and code formatting
- **Development Tools:** Pre-commit hooks, syntax validation, and automated checks
- **Cloud Ready:** Production deployment to Google Cloud Run

## Quick Start

**Prerequisites:** Node 18+, Python 3.12.3, `uv` ([install](https://docs.astral.sh/uv/)), Google Cloud project with Firestore

### Local Development

```bash
# 1. Setup dev tools (pre-commit hooks, linting)
./scripts/setup-dev-tools.sh

# 2. Configure environment
# Create backend/.env with:
#   - GOOGLE_CLOUD_PROJECT=your-project-id
#   - FIRESTORE_DATABASE=family-tree
#   - JWT_SECRET=your-secret-key
#   - GCS_BUCKET_NAME=your-bucket-name  # For profile pictures
#   - MAX_UPLOAD_SIZE_MB=5  # Optional, defaults to 5MB
# Create frontend/.env.local with:
#   - NEXT_PUBLIC_API_BASE=http://localhost:8080

# 3. Start backend
cd backend && uv venv --python 3.12.3 && uv sync
uv run uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload

# 4. Start frontend (in new terminal)
cd frontend && npm install && npm run dev
```

**Or use Docker:** `docker compose up --build`

**Access:** http://localhost:3000

## 🚀 Deployment

**Deploy your own instance:** See [Forked Deployment Guide](docs/FORKED_DEPLOYMENT.md)

**Quick steps:** Fork → Configure env vars → Run `gcp_bootstrap_family_tree.sh` → Initialize Firestore → Create admin → Deploy via GitHub Actions

**Key scripts in `backend/scripts/`:**
- `gcp_bootstrap_family_tree.sh` - GCP infrastructure setup
- `initialize_collections.py` - Firestore database init
- `seed_admin.py` - Create admin account
- `populate_dummy_data.py` - Test data (optional)

**Documentation:**
- 📖 [Forked Deployment Guide](docs/FORKED_DEPLOYMENT.md) - Complete walkthrough
- 🔧 [Backend Scripts Reference](docs/BACKEND_SCRIPTS.md) - Script usage details
- ☁️ [Deployment Guide](docs/DEPLOYMENT.md) - CI/CD and cloud setup

## Testing

```bash
# Backend
cd backend && uv run pytest --cov=app

# Frontend
cd frontend && npm test

# All quality checks
pre-commit run --all-files
```

## Documentation

- **[Architecture Overview](docs/ARCHITECTURE.md)** - Technical architecture, data flow, and sequence diagrams
- **[Screenshots](docs/SCREENSHOTS.md)** - Application screenshots and UI examples
- **[Bulk Upload Guide](docs/BULK_UPLOAD.md)** - Instructions for bulk uploading family members from JSON files
- **[Deployment Guide](docs/DEPLOYMENT.md)** - CI/CD setup, Docker configuration, and cloud deployment
- **[Event Notifications](docs/EVENT_NOTIFICATIONS.md)** - Automated email notifications setup and configuration
- **[GitHub Actions Notifications](docs/GITHUB_ACTIONS_NOTIFICATIONS.md)** - Cloud-based automated notifications setup

## Contributing

1. Run `./scripts/setup-dev-tools.sh` to install pre-commit hooks
2. Read [Contributing Guide](docs/CONTRIBUTING.md) for workflow and standards
3. Check [Architecture Overview](docs/ARCHITECTURE.md) for codebase understanding

## License

**AGPLv3 (default):** Open source use. Network deployment requires sharing source code. See [LICENSE](LICENSE).

**Commercial license available** for proprietary use. Contact: [your-email@example.com]

See [COMMERCIAL.md](docs/COMMERCIAL.md) for details.
