# Contributing to Family Tree

Thank you for your interest in contributing to the Family Tree project! This guide will help you get started with development and ensure your contributions follow our quality standards.

## First-time Setup

### 1. Install Development Tools
```bash
./setup-dev-tools.sh
```

This script installs all necessary development tools including:
- Pre-commit hooks for code quality
- JSON/YAML syntax validation
- TypeScript type checking
- ESLint for frontend code quality
- Python formatting tools (Black, Ruff)

### 2. Verify Pre-commit Hooks
```bash
pre-commit run --all-files
```

This ensures all quality checks are working correctly before you start development.

## Development Workflow

### 1. Create a Feature Branch
```bash
git checkout -b feature/your-feature-name
```

Use descriptive branch names that clearly indicate what feature or fix you're working on.

### 2. Make Your Changes

The pre-commit hooks will automatically run when you commit and will:
- Validate JSON/YAML syntax (prevents package.json errors)
- Format Python code with Black and Ruff
- Check TypeScript types
- Run ESLint on frontend code
- Check for merge conflicts and large files

### 3. Run Tests Before Pushing

#### Backend Tests
```bash
cd backend && uv run pytest
```

#### Frontend Tests
```bash
cd frontend && npm test
```

#### Code Quality Checks
```bash
cd frontend && npm run lint && npm run type-check
```

### 4. Commit and Push

Tests will run automatically on push via GitHub Actions. The CI/CD pipeline will:
- Run all backend tests with coverage requirements
- Validate frontend build
- Deploy to staging environment (if configured)

## Manual Quality Checks

### Syntax Validation
```bash
# Check all files for syntax errors
pre-commit run check-json --all-files
pre-commit run check-yaml --all-files

# Validate specific files
python -m json.tool frontend/package.json  # JSON validation
```

### Code Formatting and Linting
```bash
# Auto-fix issues
cd frontend && npm run lint:fix  # Fix ESLint issues
cd backend && uv run ruff --fix  # Fix Python issues

# Check without fixing
cd frontend && npm run lint        # ESLint checks
cd frontend && npm run type-check  # TypeScript validation
cd backend && uv run ruff check    # Python linting
cd backend && uv run black --check .  # Code formatting check
```

## Code Standards

### Python (Backend)
- Follow PEP 8 style guidelines (enforced by Black and Ruff)
- Write comprehensive tests for new features
- Maintain test coverage above 50%
- Use type hints where appropriate
- Write clear docstrings for functions and classes

### TypeScript (Frontend)
- Follow ESLint configuration rules
- Use TypeScript for type safety
- Write meaningful component and function names
- Test interactive components
- Follow React best practices

### General Guidelines
- Write clear, descriptive commit messages
- Keep commits focused and atomic
- Update documentation for new features
- Add tests for bug fixes
- Ensure all CI checks pass before requesting review

## Development Tools Reference

### Pre-commit Hooks
The project uses pre-commit hooks to maintain code quality:

```bash
# Install hooks (done automatically by setup script)
pre-commit install
pre-commit install --hook-type pre-push

# Run hooks manually
pre-commit run --all-files

# Update hook versions
pre-commit autoupdate
```

### Testing Commands
```bash
# Backend comprehensive testing
cd backend
uv run pytest --cov=app --cov-report=html

# Frontend testing
cd frontend
npm test
npm run test:watch  # Watch mode for development

# End-to-end testing (if configured)
npm run test:e2e
```

### Local Development
```bash
# Start backend (Python)
cd backend
uv run uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload

# Start frontend (Node.js)
cd frontend
npm run dev

# Docker development environment
docker compose up --build
```

## Getting Help

- **Issues**: Check existing [GitHub Issues](https://github.com/r39132/family-tree/issues) or create a new one
- **Discussions**: Use GitHub Discussions for questions and ideas
- **Documentation**: Refer to the [Architecture Overview](docs/ARCHITECTURE.md) for technical details

## Pull Request Process

1. **Fork** the repository and create your feature branch
2. **Implement** your changes following the code standards
3. **Test** your changes thoroughly
4. **Update** documentation if needed
5. **Submit** a pull request with a clear description of changes
6. **Respond** to review feedback promptly

### Pull Request Checklist
- [ ] All tests pass locally
- [ ] Pre-commit hooks pass
- [ ] Documentation updated (if applicable)
- [ ] Commit messages are clear and descriptive
- [ ] Changes are focused and atomic
- [ ] No merge conflicts with main branch

Thank you for contributing to Family Tree! 🌳
