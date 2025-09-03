#!/bin/bash
# Setup GitHub secrets for email functionality
# Run this script to add all required SMTP secrets to your GitHub repository

set -e

REPO="r39132/family-tree"

echo "🔧 Setting up GitHub secrets for email functionality..."
echo "Repository: $REPO"
echo ""

# Check if gh CLI is installed
if ! command -v gh &> /dev/null; then
    echo "❌ GitHub CLI (gh) is not installed"
    echo "📥 Install it: brew install gh"
    exit 1
fi

# Check if user is authenticated
if ! gh auth status &> /dev/null; then
    echo "❌ Not authenticated with GitHub CLI"
    echo "🔐 Run: gh auth login"
    exit 1
fi

echo "✅ GitHub CLI is ready"
echo ""

# Set secrets
echo "📝 Adding SMTP secrets..."

gh secret set SMTP_HOST --body "smtp.gmail.com" --repo "$REPO"
echo "✅ SMTP_HOST set"

gh secret set SMTP_PORT --body "587" --repo "$REPO"
echo "✅ SMTP_PORT set"

gh secret set SMTP_USER --body "r39132@gmail.com" --repo "$REPO"
echo "✅ SMTP_USER set"

gh secret set SMTP_PASSWORD --body "twpb rdzd oljn deey" --repo "$REPO"
echo "✅ SMTP_PASSWORD set"

gh secret set EMAIL_FROM --body "r39132@gmail.com" --repo "$REPO"
echo "✅ EMAIL_FROM set"

gh secret set EMAIL_FROM_NAME --body "Family Tree Admin" --repo "$REPO"
echo "✅ EMAIL_FROM_NAME set"

echo ""
echo "🎉 All email secrets have been added to GitHub!"
echo ""
echo "📋 Next steps:"
echo "1. Commit and push the updated CI/CD workflow"
echo "2. Deploy to trigger the updated environment variables"
echo "3. Test email functionality in production"
echo ""
echo "🔗 Verify secrets at: https://github.com/$REPO/settings/secrets/actions"
