#!/usr/bin/env bash

set -euo pipefail

PART=""
DRY_RUN=false
INCLUDE_DIFF=false
JSON=false
RELEASE_DATE=""
REPO_ROOT="."
MAP_PATH=".github/version-map.yml"

usage() {
    cat <<'EOF'
Usage: version-bump.sh --part <patch|minor|major> [options]

Manifest-driven version bump for Spec Kit.

Options:
  --part <value>         Required. One of: patch, minor, major
  --dry-run              Preview changes without writing files
  --include-diff         Include unified diff preview in output
  --release-date <date>  Optional changelog date (YYYY-MM-DD)
  --repo-root <path>     Repository root (default: .)
  --map <path>           Version map manifest path (default: .github/version-map.yml)
  --json                 Emit compact JSON output
  --help, -h             Show this help message
EOF
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        --part)
            if [[ $# -lt 2 ]]; then
                echo "ERROR: --part requires a value." >&2
                exit 1
            fi
            PART="$2"
            shift 2
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --include-diff)
            INCLUDE_DIFF=true
            shift
            ;;
        --release-date)
            if [[ $# -lt 2 ]]; then
                echo "ERROR: --release-date requires a value." >&2
                exit 1
            fi
            RELEASE_DATE="$2"
            shift 2
            ;;
        --repo-root)
            if [[ $# -lt 2 ]]; then
                echo "ERROR: --repo-root requires a value." >&2
                exit 1
            fi
            REPO_ROOT="$2"
            shift 2
            ;;
        --map)
            if [[ $# -lt 2 ]]; then
                echo "ERROR: --map requires a value." >&2
                exit 1
            fi
            MAP_PATH="$2"
            shift 2
            ;;
        --json)
            JSON=true
            shift
            ;;
        --help|-h)
            usage
            exit 0
            ;;
        *)
            echo "ERROR: Unknown option '$1'." >&2
            usage >&2
            exit 1
            ;;
    esac
done

if [[ -z "$PART" ]]; then
    echo "ERROR: --part is required." >&2
    usage >&2
    exit 1
fi
case "$PART" in
    patch|minor|major)
        ;;
    *)
        echo "ERROR: --part must be one of: patch, minor, major." >&2
        exit 1
        ;;
esac

PYTHON_BIN=""
if command -v python3 >/dev/null 2>&1; then
    PYTHON_BIN="python3"
elif command -v python >/dev/null 2>&1; then
    PYTHON_BIN="python"
else
    echo "ERROR: Python interpreter not found (expected 'python3' or 'python')." >&2
    exit 1
fi

cmd=(
    "$PYTHON_BIN"
    scripts/python/version-orchestrator.py
    bump
    --repo-root "$REPO_ROOT"
    --map "$MAP_PATH"
    --part "$PART"
)

if [[ -n "$RELEASE_DATE" ]]; then
    cmd+=(--release-date "$RELEASE_DATE")
fi
if [[ "$DRY_RUN" == true ]]; then
    cmd+=(--dry-run)
fi
if [[ "$INCLUDE_DIFF" == true ]]; then
    cmd+=(--include-diff)
fi
if [[ "$JSON" == true ]]; then
    cmd+=(--json)
fi

"${cmd[@]}"
