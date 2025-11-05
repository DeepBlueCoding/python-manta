#!/usr/bin/env bash
# Release preparation script for python-manta
# Usage: ./tools/prepare_release.sh <new_version>
# Example: ./tools/prepare_release.sh 0.2.0

set -euo pipefail

if [ $# -eq 0 ]; then
    echo "Usage: $0 <new_version>"
    echo "Example: $0 0.2.0"
    exit 1
fi

NEW_VERSION=$1
ROOT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)

# Validate version format (basic SemVer check)
if ! [[ $NEW_VERSION =~ ^[0-9]+\.[0-9]+\.[0-9]+(-[a-zA-Z0-9.]+)?$ ]]; then
    echo "Error: Invalid version format. Expected: X.Y.Z or X.Y.Z-prerelease"
    echo "Examples: 1.0.0, 0.2.0, 1.0.0-beta.1"
    exit 1
fi

echo "🚀 Preparing release v${NEW_VERSION}"
echo "=================================="

# Check we're on main branch
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
if [ "$CURRENT_BRANCH" != "main" ] && [ "$CURRENT_BRANCH" != "master" ]; then
    echo "⚠️  Warning: You're on branch '$CURRENT_BRANCH', not 'main' or 'master'"
    read -p "Continue anyway? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Check for uncommitted changes
if ! git diff-index --quiet HEAD --; then
    echo "❌ Error: You have uncommitted changes. Please commit or stash them first."
    git status --short
    exit 1
fi

# Check if CHANGELOG has unreleased section
if ! grep -q "\[Unreleased\]" "${ROOT_DIR}/CHANGELOG.md"; then
    echo "⚠️  Warning: No [Unreleased] section found in CHANGELOG.md"
    echo "   You may need to add release notes manually."
fi

echo ""
echo "📝 Step 1: Update CHANGELOG.md"
echo "------------------------------"

# Get today's date
TODAY=$(date +%Y-%m-%d)

# Check if version already exists in changelog
if grep -q "\[${NEW_VERSION}\]" "${ROOT_DIR}/CHANGELOG.md"; then
    echo "❌ Error: Version ${NEW_VERSION} already exists in CHANGELOG.md"
    exit 1
fi

# Create a backup
cp "${ROOT_DIR}/CHANGELOG.md" "${ROOT_DIR}/CHANGELOG.md.backup"

# Update the changelog
# Replace ## [Unreleased] with ## [Unreleased]\n\n## [NEW_VERSION] - DATE
# This is a simplified approach - you may need to manually edit

echo "ℹ️  Please manually update CHANGELOG.md:"
echo "   1. Move content from [Unreleased] to [${NEW_VERSION}] - ${TODAY}"
echo "   2. Leave [Unreleased] section empty for future changes"
echo ""
read -p "Press Enter when you've updated CHANGELOG.md (or Ctrl+C to cancel)..."

# Verify changelog was updated
if ! grep -q "\[${NEW_VERSION}\]" "${ROOT_DIR}/CHANGELOG.md"; then
    echo "❌ Error: Version ${NEW_VERSION} not found in CHANGELOG.md"
    echo "   Restoring backup..."
    mv "${ROOT_DIR}/CHANGELOG.md.backup" "${ROOT_DIR}/CHANGELOG.md"
    exit 1
fi

rm "${ROOT_DIR}/CHANGELOG.md.backup"
echo "✅ CHANGELOG.md updated"

echo ""
echo "📝 Step 2: Update version in pyproject.toml"
echo "-------------------------------------------"

# Update version in pyproject.toml
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    sed -i '' "s/^version = \".*\"/version = \"${NEW_VERSION}\"/" "${ROOT_DIR}/pyproject.toml"
else
    # Linux
    sed -i "s/^version = \".*\"/version = \"${NEW_VERSION}\"/" "${ROOT_DIR}/pyproject.toml"
fi

# Verify
UPDATED_VERSION=$(grep "^version = " "${ROOT_DIR}/pyproject.toml" | cut -d'"' -f2)
if [ "$UPDATED_VERSION" != "$NEW_VERSION" ]; then
    echo "❌ Error: Failed to update version in pyproject.toml"
    exit 1
fi

echo "✅ pyproject.toml updated to version ${NEW_VERSION}"

echo ""
echo "📝 Step 3: Review changes"
echo "------------------------"
git diff pyproject.toml CHANGELOG.md

echo ""
echo "🎯 Step 4: Commit and tag"
echo "------------------------"
read -p "Commit these changes? (y/N) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    git add pyproject.toml CHANGELOG.md
    git commit -m "chore: release v${NEW_VERSION}"
    echo "✅ Changes committed"

    echo ""
    read -p "Create tag v${NEW_VERSION}? (y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        git tag -a "v${NEW_VERSION}" -m "Release v${NEW_VERSION}"
        echo "✅ Tag v${NEW_VERSION} created"

        echo ""
        echo "🚀 Next steps:"
        echo "1. Push changes:  git push origin ${CURRENT_BRANCH}"
        echo "2. Push tag:      git push origin v${NEW_VERSION}"
        echo "3. GitHub Actions will automatically build and publish to PyPI"
        echo "4. Create GitHub release at: https://github.com/equilibrium-coach/python-manta/releases/new?tag=v${NEW_VERSION}"
    else
        echo "ℹ️  Tag not created. You can create it manually later with:"
        echo "   git tag -a v${NEW_VERSION} -m \"Release v${NEW_VERSION}\""
    fi
else
    echo "ℹ️  Changes not committed. Review and commit manually."
fi

echo ""
echo "✅ Release preparation complete!"
