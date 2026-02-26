#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(CDPATH="" cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_SCRIPT="$SCRIPT_DIR/../python/template-instruction-contract.py"

if command -v uv >/dev/null 2>&1; then
  uv run python "$PYTHON_SCRIPT" "$@"
  exit $?
fi

command -v python3 >/dev/null 2>&1 || { echo "Error: python3 not found. Please install Python 3"; exit 1; }

python3 "$PYTHON_SCRIPT" "$@"
