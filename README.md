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
- **Frontend:** Next.js (TypeScript) with nature‑themed UI
- **Backend:** FastAPI (Python 3.12.3) with JWT authentication
- **Database:** Google Firestore
- **Deployment:** Docker + GitHub Actions CI/CD to Google Cloud Run

## Features

- **Authentication:** Login, register with invite codes, password reset
- **Family Tree:** Visual tree with CRUD operations, member relationships
- **Map Integration:** Optional Google Maps integration for member locations
- **Quality Assurance:** Comprehensive testing, linting, and code formatting
- **Cloud Ready:** Production deployment to Google Cloud Run

## Quick Start

### Prerequisites

- Node 18+ and npm
- Python 3.12.3
- `uv` package manager ([install guide](https://docs.astral.sh/uv/))
- Google Cloud project with Firestore database

### Environment Setup

1. **Backend configuration** - Create `backend/.env`:
   ```bash
   GOOGLE_CLOUD_PROJECT=your-project-id
   FIRESTORE_DATABASE=family-tree
   JWT_SECRET_KEY=your-secret-key
   # Optional: Google Maps integration
   ENABLE_MAP=true
   GOOGLE_MAPS_API_KEY=your-maps-api-key
   ```

2. **Frontend configuration** - Create `frontend/.env.local`:
   ```bash
   NEXT_PUBLIC_API_BASE=http://localhost:8080
   ```

### Development

1. **Setup Python environment:**
   ```bash
   cd backend
   uv venv --python 3.12.3
   uv sync
   ```

2. **Run backend:**
   ```bash
   cd backend
   uv run uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload
   ```

3. **Run frontend:**
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

4. **Access application:** http://localhost:3000

### Docker Compose (Alternative)

```bash
docker compose up --build
```

## Testing

```bash
cd backend
uv run pytest --cov=app
```

## Deployment

The project includes GitHub Actions workflow for automatic deployment to Google Cloud Run. See [CI/CD documentation](docs/ARCHITECTURE.md) for setup details.

## Documentation

- **[Architecture Overview](docs/ARCHITECTURE.md)** - Technical architecture, data flow, and sequence diagrams
- **[Screenshots](docs/SCREENSHOTS.md)** - Application screenshots and UI examples

## Contributing

1. Install pre-commit hooks:
   ```bash
   cd backend
   uv run pre-commit install
   uv run pre-commit install --hook-type pre-push
   ```

2. Run tests before committing:
   ```bash
   uv run pytest
   ```

## License

This project is dual-licensed:

### AGPLv3 (Default)

This software is licensed under the GNU Affero General Public License v3.0 (AGPLv3) for open source use. See the [LICENSE](LICENSE) file for details.

Key requirements under AGPLv3:
- **Source Code Availability**: If you run this software on a server and allow users to interact with it over a network, you must provide the source code to those users
- **Copyleft**: Any modifications or derivative works must also be licensed under AGPLv3
- **Attribution**: You must retain all copyright notices and license information

### Commercial License

For commercial use, closed-source derivatives, or applications where AGPLv3 requirements cannot be met, a separate commercial license is available.

**Commercial license benefits:**
- No requirement to disclose source code
- Freedom to create proprietary derivatives
- Commercial support and customization available

For commercial licensing inquiries, please contact: [your-email@example.com]
