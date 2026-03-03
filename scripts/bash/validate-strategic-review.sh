#!/usr/bin/env bash
# validate-strategic-review.sh - validate strategic review artifact and emit blockers.

set -euo pipefail

if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
  echo "Usage: $(basename "$0") [FILE_PATH] [PROJECT_DIR]"
  echo ""
  echo "Validate .ideas/evaluation-results.md and emit .ideas/launch-blockers.md when needed."
  echo ""
  echo "Arguments:"
  echo "  FILE_PATH    Path to strategic review markdown file (default: .ideas/evaluation-results.md)"
  echo "  PROJECT_DIR  Project root directory for config/artifact resolution (default: current directory)"
  echo ""
  echo "Configuration precedence:"
  echo "  1) Built-in defaults"
  echo "  2) .specify/spec-kit.yml"
  echo "  3) .specify/spec-kit.local.yml"
  echo "  4) SPECIFY_CONFIG__STRATEGIC_REVIEW__... env overrides"
  exit 0
fi

FILE_PATH="${1:-.ideas/evaluation-results.md}"
PROJECT_DIR="${2:-.}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RUNTIME_SCRIPT="$SCRIPT_DIR/../strategic-review-runtime.py"

if [ ! -f "$RUNTIME_SCRIPT" ]; then
  echo "Error: strategic-review runtime helper not found at $RUNTIME_SCRIPT" >&2
  exit 1
fi

if command -v uv >/dev/null 2>&1; then
  uv run python "$RUNTIME_SCRIPT" \
    --mode validate \
    --file "$FILE_PATH" \
    --project-root "$PROJECT_DIR"
  exit $?
fi

if ! command -v python3 >/dev/null 2>&1; then
  echo "Error: neither 'uv' nor 'python3' is available in PATH." >&2
  exit 1
fi

if ! python3 -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 9) else 1)" >/dev/null 2>&1; then
  echo "Error: python3 must be Python >= 3.9." >&2
  exit 1
fi

python3 "$RUNTIME_SCRIPT" \
  --mode validate \
  --file "$FILE_PATH" \
  --project-root "$PROJECT_DIR"
