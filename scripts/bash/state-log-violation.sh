#!/usr/bin/env bash
set -euo pipefail

PHASE="${1:-unknown}"
PRINCIPLE="${2:-unknown}"
MESSAGE="${3:-}"
SEVERITY="${4:-high}"
SOURCE="${5:-validator}"

STATE_FILE=".spec-kit/state.yaml"
TEMP_FILE=".spec-kit/.state.yaml.tmp"

if [ -z "$MESSAGE" ]; then
  echo "Usage: state-log-violation.sh <phase> <principle> <message> [severity] [source]"
  exit 1
fi

command -v yq >/dev/null 2>&1 || { echo "Error: yq not found. Install: brew install yq || sudo apt install yq"; exit 1; }

if [ ! -f "$STATE_FILE" ]; then
  echo "Error: state.yaml not found. Run state-init.sh first."
  exit 1
fi

timestamp="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"

yq eval ".violations += [{\"timestamp\":\"$timestamp\",\"phase\":\"$PHASE\",\"principle\":\"$PRINCIPLE\",\"message\":\"$MESSAGE\",\"severity\":\"$SEVERITY\",\"source\":\"$SOURCE\"}]" "$STATE_FILE" > "$TEMP_FILE"
mv "$TEMP_FILE" "$STATE_FILE"
