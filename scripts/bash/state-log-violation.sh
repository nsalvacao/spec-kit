#!/usr/bin/env bash
set -euo pipefail

PHASE="${1:-unknown}"
PRINCIPLE="${2:-unknown}"
MESSAGE="${3:-}"
SEVERITY="${4:-high}"
SOURCE="${5:-validator}"

STATE_FILE=".spec-kit/state.yaml"
SCRIPT_DIR="$(CDPATH="" cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_SCRIPT="$SCRIPT_DIR/../python/state-update.py"

if [ -z "$MESSAGE" ]; then
  echo "Usage: state-log-violation.sh <phase> <principle> <message> [severity] [source]"
  exit 1
fi

command -v python3 >/dev/null 2>&1 || { echo "Error: python3 not found. Please install Python 3"; exit 1; }

if [ ! -f "$STATE_FILE" ]; then
  echo "Error: state.yaml not found. Run state-init.sh first."
  exit 1
fi

python3 "$PYTHON_SCRIPT" \
  --file "$STATE_FILE" \
  --operation log-violation \
  --violation-phase "$PHASE" \
  --violation-principle "$PRINCIPLE" \
  --violation-message "$MESSAGE" \
  --violation-severity "$SEVERITY" \
  --violation-source "$SOURCE"
