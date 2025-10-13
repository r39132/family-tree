#!/bin/bash

set -e

echo "🧹 Starting Phase 2 Repository Cleanup..."
echo ""
echo "Note: Most debug/temp files were already removed in Phase 1."
echo "This script focuses on organization and remaining cleanup."
echo ""

# Phase 1: Remove redundant pre-commit configs
echo "Step 1: Removing redundant pre-commit configs from backend..."
git rm backend/pre-commit-config.yaml backend/pre-commit-config.yaml.backup
echo "✓ Removed 2 redundant pre-commit config files"
echo ""

# Phase 2: Organize shell scripts
echo "Step 2: Organizing shell scripts..."
git mv cleanup-repo.sh scripts/
git mv setup-dev-tools.sh scripts/
echo "✓ Moved 2 shell scripts to scripts/"
echo ""

# Phase 3: Move cleanup docs to docs folder
echo "Step 3: Moving cleanup documentation to docs/..."
git mv CLEANUP_GUIDE.md docs/
git mv CLEANUP_SUMMARY.md docs/
echo "✓ Moved 2 cleanup documents to docs/"
echo ""

# Phase 4: Clean up local untracked cache files
echo "Step 4: Cleaning local cache files (not tracked in git)..."
CLEANED=0

# Remove .DS_Store files
if [ -n "$(find . -name ".DS_Store" 2>/dev/null)" ]; then
    find . -name ".DS_Store" -delete 2>/dev/null
    echo "  ✓ Removed .DS_Store files"
    CLEANED=1
fi

# Remove __pycache__ directories
if [ -n "$(find . -name "__pycache__" -type d 2>/dev/null)" ]; then
    find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
    echo "  ✓ Removed __pycache__ directories"
    CLEANED=1
fi

# Remove .pyc files
if [ -n "$(find . -name "*.pyc" 2>/dev/null)" ]; then
    find . -name "*.pyc" -delete 2>/dev/null
    echo "  ✓ Removed .pyc files"
    CLEANED=1
fi

if [ $CLEANED -eq 0 ]; then
    echo "  ✓ No cache files found to clean"
fi
echo ""

# Phase 5: Stage the cleanup script itself for removal after commit
echo "Step 5: Adding this cleanup script to be removed..."
git add cleanup-phase-2.sh
echo "✓ Staged cleanup-phase-2.sh (will be removed in commit)"
echo ""

echo "✅ Phase 2 cleanup complete!"
echo ""
echo "Summary:"
echo "  - Removed: 2 redundant pre-commit config files"
echo "  - Moved: 2 shell scripts, 2 docs"
echo "  - Cleaned: Local cache files (.DS_Store, __pycache__, .pyc)"
echo "  - Total git changes: 6 files"
echo ""
echo "Next steps:"
echo "  1. Review changes: git status"
echo "  2. Remove this script: git rm cleanup-phase-2.sh"
echo "  3. Commit: git commit -m 'chore: phase 2 cleanup - organize scripts and docs, remove redundant configs'"
echo "  4. Push: git push origin main"
