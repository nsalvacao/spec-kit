#!/usr/bin/env bash
set -euo pipefail

STATE_FILE=".spec-kit/state.yaml"
TEMP_FILE=".spec-kit/.state.yaml.tmp"
EXPR="${1:-}"

if [ -z "$EXPR" ]; then
  echo "Usage: state-update.sh '<yq_expression>'"
  exit 1
fi

command -v yq >/dev/null 2>&1 || { echo "Error: yq not found. Install: brew install yq || sudo apt install yq"; exit 1; }

if [ ! -f "$STATE_FILE" ]; then
  echo "Error: state.yaml not found. Run state-init.sh first."
  exit 1
fi

yq eval ".violations //= [] | $EXPR" "$STATE_FILE" > "$TEMP_FILE"
mv "$TEMP_FILE" "$STATE_FILE"
