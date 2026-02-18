#!/usr/bin/env bash
set -euo pipefail

FILE_PATH="${1:-.spec-kit/idea_selection.md}"
STATE_LOG="scripts/bash/state-log-violation.sh"

if [ ! -f "$FILE_PATH" ]; then
  echo "Error: idea_selection not found at $FILE_PATH"
  if [ -x "$STATE_LOG" ]; then
    "$STATE_LOG" "select" "Framework-Driven Development" "idea_selection.md missing" "critical" "validate-airice"
  fi
  exit 1
fi

header_line=$(rg -n "^\|" "$FILE_PATH" | head -1 | cut -d: -f2- || true)
if ! echo "$header_line" | rg -q "Reach" || ! echo "$header_line" | rg -q "Impact" || ! echo "$header_line" | rg -q "Confidence" || ! echo "$header_line" | rg -q "Data_Readiness" || ! echo "$header_line" | rg -q "Effort" || ! echo "$header_line" | rg -q "Risk"; then
  echo "Error: AI-RICE scoring table header missing required columns"
  if [ -x "$STATE_LOG" ]; then
    "$STATE_LOG" "select" "Framework-Driven Development" "AI-RICE table missing required columns" "high" "validate-airice"
  fi
  exit 1
fi

if ! echo "$header_line" | rg -q "Norm_Score"; then
  echo "Error: AI-RICE scoring table missing Norm_Score column (normalized 0-100 score)"
  if [ -x "$STATE_LOG" ]; then
    "$STATE_LOG" "select" "Framework-Driven Development" "AI-RICE table missing Norm_Score column" "high" "validate-airice"
  fi
  exit 1
fi

rows=$(rg -n "^\|" "$FILE_PATH" | sed -n '3,$p' | rg -c "\|" || true)
if [ "$rows" -lt 1 ]; then
  echo "Error: AI-RICE scoring table has no data rows"
  if [ -x "$STATE_LOG" ]; then
    "$STATE_LOG" "select" "Framework-Driven Development" "AI-RICE table has no data rows" "high" "validate-airice"
  fi
  exit 1
fi

required_breakdown=("Reach" "Impact" "Confidence" "Data_Readiness" "Effort" "Risk")
for item in "${required_breakdown[@]}"; do
  if ! rg -q "\*\*$item\*\*:" "$FILE_PATH"; then
    echo "Error: Missing dimensional breakdown for $item"
    if [ -x "$STATE_LOG" ]; then
      "$STATE_LOG" "select" "Traceability First" "Missing dimensional breakdown: $item" "high" "validate-airice"
    fi
    exit 1
  fi
done

echo "AI-RICE validation passed"
