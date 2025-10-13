#!/bin/bash

echo "Setting up development tools..."

# Install pre-commit if not already installed
if ! command -v pre-commit &> /dev/null; then
    echo "Installing pre-commit..."
    pip install pre-commit
fi

# Install pre-commit hooks
echo "Installing pre-commit hooks..."
pre-commit install
pre-commit install --hook-type pre-push

# Install frontend dependencies if needed
if [ ! -d "frontend/node_modules" ]; then
    echo "Installing frontend dependencies..."
    cd frontend && npm install && cd ..
fi

# Install ESLint dependencies
echo "Installing ESLint dependencies..."
cd frontend
npm install --save-dev eslint eslint-config-next @typescript-eslint/parser @typescript-eslint/eslint-plugin
cd ..

echo "✅ Development tools setup complete!"
echo ""
echo "Now you have:"
echo "  - JSON/YAML syntax checking"
echo "  - TypeScript type checking"
echo "  - ESLint for code quality"
echo "  - Python formatting and linting"
echo "  - Automated tests on push"
echo ""
echo "To manually run checks:"
echo "  pre-commit run --all-files    # Run all checks"
echo "  cd frontend && npm run lint   # Frontend linting"
echo "  cd frontend && npm run type-check  # TypeScript check"
