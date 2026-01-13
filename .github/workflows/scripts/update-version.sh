#!/usr/bin/env bash
set -euo pipefail

# update-version.sh
# Update version in pyproject.toml (for release artifacts only)
# Usage: update-version.sh <version>

if [[ $# -ne 1 ]]; then
  echo "Usage: $0 <version>" >&2
  exit 1
fi

VERSION="$1"

# Remove 'v' prefix for Python versioning
PYTHON_VERSION=${VERSION#v}
if [[ $PYTHON_VERSION =~ ^([0-9]+\.[0-9]+\.[0-9]+)-fork\.([0-9]+)$ ]]; then
  PYTHON_VERSION="${BASH_REMATCH[1]}.post${BASH_REMATCH[2]}"
fi

if [ -f "pyproject.toml" ]; then
  sed -i "s/version = \".*\"/version = \"$PYTHON_VERSION\"/" pyproject.toml
  echo "Updated pyproject.toml version to $PYTHON_VERSION (for release artifacts only)"
else
  echo "Warning: pyproject.toml not found, skipping version update"
fi
