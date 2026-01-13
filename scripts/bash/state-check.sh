#!/usr/bin/env bash
set -euo pipefail

REQUIRED_PHASE="${1:-}"
STATE_FILE=".spec-kit/state.yaml"

if [ -z "$REQUIRED_PHASE" ]; then
  echo "Usage: state-check.sh <required_phase>"
  exit 1
fi

command -v yq >/dev/null 2>&1 || { echo "Error: yq not found. Install: brew install yq || sudo apt install yq"; exit 1; }

if [ ! -f "$STATE_FILE" ]; then
  echo "Error: state.yaml not found. Run state-init.sh first."
  exit 1
fi

if ! yq eval ".phases_completed | contains([\"$REQUIRED_PHASE\"])" "$STATE_FILE" | grep -q "true"; then
  echo "Error: Phase '$REQUIRED_PHASE' must be completed first."
  exit 1
fi
