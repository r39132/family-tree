# Deployment Tools

This document covers the deployment infrastructure, development tools, and automated processes used in the Family Tree project.

## GitHub Actions CI/CD

The project includes a comprehensive GitHub Actions workflow for automatic deployment to Google Cloud Run.

### Workflow Overview
The CI/CD pipeline includes:
- **Backend CI**: Python testing, linting, and coverage reporting
- **Coverage Badge**: Automatic test coverage badge generation
- **Backend Deploy**: Docker build and deployment to Google Cloud Run
- **Frontend Deploy**: Next.js build and deployment to Google Cloud Run

### Workflow Configuration
See [CI/CD documentation](ARCHITECTURE.md) for detailed setup instructions and architecture diagrams.

## Development Tools

This project includes comprehensive development tools to prevent syntax errors and maintain code quality:

### Automated Checks
- **Pre-commit hooks** validate code before each commit
- **JSON/YAML validation** prevents configuration file errors
- **TypeScript type checking** catches type errors early
- **ESLint** enforces frontend code standards
- **Python formatting** with Black and Ruff
- **Test coverage** tracking with badges

### Syntax Error Prevention
The setup prevents common issues like:
- `package.json` syntax errors that break Docker builds
- TypeScript compilation errors
- Python import/syntax issues
- YAML configuration problems
- Merge conflicts and large file commits

### Setup Commands
```bash
# One-time setup (installs all tools)
./setup-dev-tools.sh

# Manual pre-commit installation
pre-commit install
pre-commit install --hook-type pre-push

# Check specific file types
python -m json.tool frontend/package.json  # Validate JSON
pre-commit run check-yaml --all-files       # Validate YAML
```

## Docker Configuration

### Backend Dockerfile
The backend uses a multi-stage Python Docker build with uv package manager:
- Base image: `python:3.12-slim`
- Package management: `uv` for fast dependency resolution
- Production optimizations: minimal image size, non-root user

### Frontend Dockerfile
The frontend uses Node.js with Next.js build optimization:
- Base image: `node:20-alpine`
- Build process: `npm ci` for production dependencies
- Static generation: Next.js optimized builds
- Port: 3000

### Docker Compose
Local development environment with:
- Backend service on port 8080
- Frontend service on port 3000
- Volume mounts for live reloading
- Environment variable configuration

## Google Cloud Run Deployment

### Prerequisites
- Google Cloud Project with billing enabled
- Firestore database configured
- Container Registry or Artifact Registry enabled
- Service account with appropriate permissions

### Required Secrets
Configure these secrets in your GitHub repository:

```bash
# Google Cloud Configuration
GCP_PROJECT_ID=your-project-id
GCP_SA_KEY=base64-encoded-service-account-key
GAR_LOCATION=us-central1
CLOUD_RUN_REGION=us-central1
CLOUD_RUN_SERVICE=family-tree-api

# SMTP Configuration (optional)
SMTP_HOST=smtp.gmail.com
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
EMAIL_FROM=noreply@yourdomain.com
EMAIL_FROM_NAME="Your App Name"
USE_EMAIL_IN_DEV=false
```

### Deployment Commands
```bash
# Manual deployment (backend)
gcloud run deploy family-tree-api \
  --image gcr.io/PROJECT_ID/family-tree-api \
  --region us-central1 \
  --platform managed \
  --allow-unauthenticated

# Manual deployment (frontend)
gcloud run deploy family-tree-web \
  --image gcr.io/PROJECT_ID/family-tree-web \
  --region us-central1 \
  --platform managed \
  --allow-unauthenticated
```

## Environment Configuration

### Backend Environment Variables
```bash
# Required
GOOGLE_CLOUD_PROJECT=your-project-id
FIRESTORE_DATABASE=family-tree
JWT_SECRET=your-jwt-secret
JWT_ALG=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60

# Optional Features
ENABLE_MAP=true
GOOGLE_MAPS_API_KEY=your-maps-api-key
REQUIRE_INVITE=false
FRONTEND_URL=https://your-frontend-domain.com

# Email Configuration (optional)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
EMAIL_FROM=noreply@yourdomain.com
EMAIL_FROM_NAME="Family Tree Admin"
USE_EMAIL_IN_DEV=true
```

### Frontend Environment Variables
```bash
# Required
NEXT_PUBLIC_API_BASE=https://your-backend-url

# Optional
NEXT_PUBLIC_GOOGLE_MAPS_API_KEY=your-maps-api-key
```

## Monitoring and Observability

### Health Checks
- Backend: `/healthz` endpoint with version and timestamp
- Frontend: Next.js built-in health monitoring
- Google Cloud Run: Automatic health checking and restart

### Logging
- Structured logging with Cloud Logging
- Error tracking and alerting
- Performance monitoring with Cloud Monitoring

### Test Coverage
- Automated test coverage reporting
- Coverage badges in README
- Minimum coverage threshold enforcement (50%)

## Local Development Tools

### Quality Assurance Tools
```bash
# Code formatting
black backend/  # Python formatting
ruff backend/   # Python linting
npm run lint --prefix frontend  # TypeScript/React linting

# Type checking
mypy backend/   # Python type checking
npm run type-check --prefix frontend  # TypeScript checking

# Testing
pytest backend/ --cov=app  # Backend tests with coverage
npm test --prefix frontend  # Frontend tests
```

### Database Tools
```bash
# Firestore emulator for local development
firebase emulators:start --only firestore

# Database backup/restore (production)
gcloud firestore export gs://your-backup-bucket
gcloud firestore import gs://your-backup-bucket/export-folder
```

## Troubleshooting

### Common Deployment Issues

1. **Docker build failures**
   - Check Dockerfile syntax
   - Verify all dependencies are listed
   - Ensure build context includes necessary files

2. **Environment variable issues**
   - Verify all required secrets are set in GitHub
   - Check environment variable names match exactly
   - Validate JSON configuration files

3. **Google Cloud authentication**
   - Verify service account permissions
   - Check JSON key is properly base64 encoded
   - Ensure billing is enabled on the project

4. **Frontend build failures**
   - Check package.json syntax with `python -m json.tool`
   - Verify all dependencies are compatible
   - Check TypeScript compilation errors

### Debugging Commands
```bash
# Check pre-commit hooks
pre-commit run --all-files

# Validate configuration files
python -m json.tool frontend/package.json
yamllint .github/workflows/ci-cd.yml

# Test Docker builds locally
docker build -t test-backend backend/
docker build -t test-frontend frontend/

# Check Google Cloud authentication
gcloud auth list
gcloud config list
```

## Security Considerations

### Secrets Management
- Use GitHub Secrets for sensitive configuration
- Rotate service account keys regularly
- Use least-privilege principle for service accounts
- Never commit sensitive data to version control

### Network Security
- Configure CORS appropriately for frontend/backend communication
- Use HTTPS in production
- Implement rate limiting on API endpoints
- Validate all input data

For more detailed information, see the [Architecture Overview](ARCHITECTURE.md) and [Contributing Guide](CONTRIBUTING.md).
