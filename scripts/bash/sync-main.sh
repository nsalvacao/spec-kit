#!/usr/bin/env bash

set -euo pipefail

APPLY=false
REMOTE="origin"

usage() {
    cat <<'EOF'
Usage: sync-main.sh [--apply] [--remote <name>] [--help]

Synchronize local main with remote main and optionally prune stale local branches.

Options:
  --apply            Delete local branches whose upstream is [gone]
  --remote <name>    Remote name to sync from (default: origin)
  --help, -h         Show this help message
EOF
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        --apply)
            APPLY=true
            shift
            ;;
        --remote)
            if [[ $# -lt 2 ]]; then
                echo "ERROR: --remote requires a value" >&2
                exit 1
            fi
            REMOTE="$2"
            shift 2
            ;;
        --help|-h)
            usage
            exit 0
            ;;
        *)
            echo "ERROR: Unknown option '$1'" >&2
            usage >&2
            exit 1
            ;;
    esac
done

if ! git rev-parse --show-toplevel >/dev/null 2>&1; then
    echo "ERROR: Not inside a git repository." >&2
    exit 1
fi

if ! git remote get-url "$REMOTE" >/dev/null 2>&1; then
    echo "ERROR: Remote '$REMOTE' not found." >&2
    exit 1
fi

echo "Fetching '$REMOTE' with prune..."
git fetch "$REMOTE" --prune

echo "Checking out 'main'..."
git checkout main

echo "Fast-forward pulling '$REMOTE/main'..."
git pull --ff-only "$REMOTE" main

mapfile -t GONE_BRANCHES < <(
    git for-each-ref --format='%(refname:short)|%(upstream:track)' refs/heads \
    | awk -F'|' '$2 ~ /gone/ {print $1}' \
    | grep -v '^main$' || true
)

if [[ ${#GONE_BRANCHES[@]} -eq 0 ]]; then
    echo "No stale local branches with [gone] upstream."
    exit 0
fi

echo "Stale local branches ([gone] upstream):"
for branch in "${GONE_BRANCHES[@]}"; do
    echo "  - $branch"
done

if [[ "$APPLY" != true ]]; then
    echo ""
    echo "Dry-run mode (default): no branches deleted."
    echo "Re-run with --apply to delete the stale branches listed above."
    exit 0
fi

echo ""
echo "Deleting stale local branches..."
for branch in "${GONE_BRANCHES[@]}"; do
    if git branch -d "$branch" >/dev/null 2>&1; then
        echo "  ✓ deleted $branch"
    else
        echo "  ✗ skipped $branch (not fully merged or deletion blocked)"
    fi
done
