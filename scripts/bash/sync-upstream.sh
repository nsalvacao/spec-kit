#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$repo_root"

if ! command -v git >/dev/null 2>&1; then
  echo "Error: git is required."
  exit 1
fi

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "Error: not inside a git repository."
  exit 1
fi

if ! git remote get-url upstream >/dev/null 2>&1; then
  git remote add upstream https://github.com/github/spec-kit.git
  echo "Added upstream remote: https://github.com/github/spec-kit.git"
fi

git fetch upstream --prune

current_branch="$(git rev-parse --abbrev-ref HEAD)"
echo "Upstream fetched."
echo "Current branch: ${current_branch}"
echo ""
echo "Next steps (choose one):"
echo "  git merge upstream/main"
echo "  git rebase upstream/main"
echo ""
echo "After resolving conflicts, run tests and push to origin."
