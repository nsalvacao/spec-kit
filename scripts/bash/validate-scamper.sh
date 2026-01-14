#!/usr/bin/env bash
set -euo pipefail

FILE_PATH="${1:-.spec-kit/ideas_backlog.md}"
STATE_LOG="scripts/bash/state-log-violation.sh"

if [ ! -f "$FILE_PATH" ]; then
  echo "Error: ideas_backlog not found at $FILE_PATH"
  if [ -x "$STATE_LOG" ]; then
    "$STATE_LOG" "ideate" "Framework-Driven Development" "ideas_backlog.md missing" "critical" "validate-scamper"
  fi
  exit 1
fi

required_lenses=(
  "SCAMPER-Substitute"
  "SCAMPER-Combine"
  "SCAMPER-Adapt"
  "SCAMPER-Modify"
  "SCAMPER-Put-to-another-use"
  "SCAMPER-Eliminate"
  "SCAMPER-Reverse"
)

missing=()
for lens in "${required_lenses[@]}"; do
  if ! rg -q "(\\*\\*Tag\\*\\*|Tag): $lens" "$FILE_PATH"; then
    missing+=("$lens")
  fi
done

if [ "${#missing[@]}" -gt 0 ]; then
  echo "Error: Missing SCAMPER lenses: ${missing[*]}"
  if [ -x "$STATE_LOG" ]; then
    "$STATE_LOG" "ideate" "Framework-Driven Development" "Missing SCAMPER lenses: ${missing[*]}" "high" "validate-scamper"
  fi
  exit 1
fi

hmw_count=$(rg -c "(\\*\\*Tag\\*\\*|Tag): HMW-" "$FILE_PATH" || true)
if [ "$hmw_count" -lt 5 ]; then
  echo "Error: Expected at least 5 HMW ideas, found $hmw_count"
  if [ -x "$STATE_LOG" ]; then
    "$STATE_LOG" "ideate" "Framework-Driven Development" "Insufficient HMW ideas: $hmw_count" "high" "validate-scamper"
  fi
  exit 1
fi

idea_count=$(rg -c "^\*\*Tag\*\*: " "$FILE_PATH" || true)
if [ "$idea_count" -lt 8 ]; then
  echo "Error: Expected at least 8 total ideas, found $idea_count"
  if [ -x "$STATE_LOG" ]; then
    "$STATE_LOG" "ideate" "Framework-Driven Development" "Insufficient total ideas: $idea_count" "high" "validate-scamper"
  fi
  exit 1
fi

non_seed_count=$(rg -c "(\\*\\*Tag\\*\\*|Tag): (SCAMPER|HMW)-" "$FILE_PATH" || true)
provenance_count=$(rg -c "^\*\*Provenance\*\*: " "$FILE_PATH" || true)
if [ "$provenance_count" -lt "$non_seed_count" ]; then
  echo "Error: Missing Provenance fields for non-seed ideas"
  if [ -x "$STATE_LOG" ]; then
    "$STATE_LOG" "ideate" "Traceability First" "Missing provenance on non-seed ideas" "high" "validate-scamper"
  fi
  exit 1
fi

echo "SCAMPER/HMW validation passed"
