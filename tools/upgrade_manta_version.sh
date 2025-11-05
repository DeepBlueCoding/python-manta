#!/usr/bin/env bash
# Helper script to upgrade the locked manta library version
#
# Usage:
#   ./tools/upgrade_manta_version.sh v3.0.3
#   ./tools/upgrade_manta_version.sh master
#   ./tools/upgrade_manta_version.sh <commit-hash>
#
# This script:
# 1. Updates .manta-version with the new version
# 2. Shows you the current python-manta version in pyproject.toml
# 3. Reminds you to update pyproject.toml to match (for releases)

set -euo pipefail

if [[ $# -ne 1 ]]; then
    echo "Usage: $0 <manta-version>"
    echo ""
    echo "Examples:"
    echo "  $0 v3.0.3        # Lock to specific release"
    echo "  $0 master        # Use latest development"
    echo "  $0 abc123def     # Lock to specific commit"
    echo ""
    echo "Current locked version:"
    grep -v '^#' .manta-version | grep -v '^[[:space:]]*$' | tail -n1
    exit 1
fi

NEW_VERSION="$1"
ROOT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
VERSION_FILE="${ROOT_DIR}/.manta-version"

# Check if it looks like a valid version/ref
if [[ ! "${NEW_VERSION}" =~ ^(v[0-9]+\.[0-9]+\.[0-9]+.*|master|[a-f0-9]{7,40})$ ]]; then
    echo "⚠️  Warning: '${NEW_VERSION}' doesn't look like a typical version tag, branch, or commit hash"
    echo "   Expected formats: v3.0.2, master, or abc123def"
    read -p "Continue anyway? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Aborted."
        exit 1
    fi
fi

# Read current version from file
OLD_VERSION=$(grep -v '^#' "${VERSION_FILE}" | grep -v '^[[:space:]]*$' | tail -n1 | tr -d '[:space:]')

if [[ "${OLD_VERSION}" == "${NEW_VERSION}" ]]; then
    echo "✅ Already at version ${NEW_VERSION}"
    exit 0
fi

# Update .manta-version file (preserve header, update last line)
echo "📝 Updating .manta-version: ${OLD_VERSION} → ${NEW_VERSION}"
sed -i.bak "$ s/${OLD_VERSION}/${NEW_VERSION}/" "${VERSION_FILE}"
rm -f "${VERSION_FILE}.bak"

echo "✅ Updated .manta-version to ${NEW_VERSION}"
echo ""

# Check python-manta version in pyproject.toml
if [[ -f "${ROOT_DIR}/pyproject.toml" ]]; then
    CURRENT_PY_VERSION=$(grep '^version = ' "${ROOT_DIR}/pyproject.toml" | sed 's/version = "\(.*\)"/\1/')
    echo "📦 Current python-manta version in pyproject.toml: ${CURRENT_PY_VERSION}"

    # If new version is a tag like v3.0.2, suggest matching python version
    if [[ "${NEW_VERSION}" =~ ^v([0-9]+\.[0-9]+\.[0-9]+.*)$ ]]; then
        SUGGESTED_PY_VERSION="${BASH_REMATCH[1]}"
        if [[ "${CURRENT_PY_VERSION}" != "${SUGGESTED_PY_VERSION}" ]]; then
            echo ""
            echo "💡 Version Synchronization Reminder:"
            echo "   You locked manta to: ${NEW_VERSION}"
            echo "   Suggested python-manta version: ${SUGGESTED_PY_VERSION}"
            echo ""
            echo "   To update pyproject.toml version:"
            echo "   sed -i 's/version = \".*\"/version = \"${SUGGESTED_PY_VERSION}\"/' pyproject.toml"
        fi
    fi
fi

echo ""
echo "✅ Done! Next steps:"
echo "   1. Test the build: ./build.sh"
echo "   2. Run tests: python run_tests.py --unit"
echo "   3. Commit: git add .manta-version && git commit -m 'chore: upgrade manta to ${NEW_VERSION}'"
