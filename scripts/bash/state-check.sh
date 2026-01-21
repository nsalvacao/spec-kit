#!/usr/bin/env bash
set -euo pipefail

REQUIRED_PHASE="${1:-}"
STATE_FILE=".spec-kit/state.yaml"
SCRIPT_DIR="$(CDPATH="" cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_SCRIPT="$SCRIPT_DIR/../python/state-update.py"

if [ -z "$REQUIRED_PHASE" ]; then
  echo "Usage: state-check.sh <required_phase>"
  exit 1
fi

command -v python3 >/dev/null 2>&1 || { echo "Error: python3 not found. Please install Python 3"; exit 1; }

if [ ! -f "$STATE_FILE" ]; then
  echo "Error: state.yaml not found. Run state-init.sh first."
  exit 1
fi

# Use Python to check if the phase is in phases_completed array
if ! python3 -c "
import yaml
import sys
with open('$STATE_FILE', 'r') as f:
    data = yaml.safe_load(f)
phases = data.get('phases_completed', [])
if '$REQUIRED_PHASE' in phases:
    sys.exit(0)
else:
    sys.exit(1)
"; then
  echo "Error: Phase '$REQUIRED_PHASE' must be completed first."
  exit 1
fi
