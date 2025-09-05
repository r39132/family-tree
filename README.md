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
- **Map Integration:** Optional Google Maps integration for member locations
- **Quality Assurance:** Comprehensive testing, linting, and code formatting
- **Development Tools:** Pre-commit hooks, syntax validation, and automated checks
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

1. **Setup development tools (recommended first step):**
   ```bash
   ./setup-dev-tools.sh
   ```
   This installs pre-commit hooks for:
   - JSON/YAML syntax validation
   - Python code formatting (Black, Ruff)
   - TypeScript type checking
   - ESLint for frontend code quality
   - Automated tests on push

2. **Setup Python environment:**
   ```bash
   cd backend
   uv venv --python 3.12.3
   uv sync
   ```

3. **Run backend:**
   ```bash
   cd backend
   uv run uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload
   ```

4. **Run frontend:**
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

5. **Access application:** http://localhost:3000

### Docker Compose (Alternative)

```bash
docker compose up --build
```

## Testing

### Backend Tests
```bash
cd backend
uv run pytest --cov=app
```

### Frontend Tests
```bash
cd frontend
npm test
```

### Syntax and Code Quality Checks
```bash
# Run all pre-commit hooks manually
pre-commit run --all-files

# Frontend specific checks
cd frontend
npm run lint        # ESLint checks
npm run type-check  # TypeScript validation

# Backend specific checks
cd backend
uv run ruff check   # Python linting
uv run black --check .  # Code formatting check
```

## Deployment

The project includes GitHub Actions workflow for automatic deployment to Google Cloud Run. See [Deployment Guide](docs/DEPLOYMENT.md) for complete setup details and troubleshooting.

## Documentation

- **[Architecture Overview](docs/ARCHITECTURE.md)** - Technical architecture, data flow, and sequence diagrams
- **[Screenshots](docs/SCREENSHOTS.md)** - Application screenshots and UI examples
- **[Contributing Guide](docs/CONTRIBUTING.md)** - Development workflow, code standards, and quality tools
- **[Deployment Guide](docs/DEPLOYMENT.md)** - CI/CD setup, Docker configuration, and cloud deployment

## Contributing

We welcome contributions! To get started:

1. **Setup development tools:** `./setup-dev-tools.sh`
2. **Read the [Contributing Guide](docs/CONTRIBUTING.md)** for detailed workflow and standards
3. **Check the [Architecture Overview](docs/ARCHITECTURE.md)** to understand the codebase

For quick development:
```bash
# Install pre-commit hooks
pre-commit install

# Run tests
cd backend && uv run pytest
cd frontend && npm test
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
