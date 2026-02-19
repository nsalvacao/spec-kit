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

# --- Semantic validation: verify formula and value ranges (issue #21) ---
# Parse table data rows, compute expected AI-RICE score, compare with stored.
# Table format: | Idea ID | Reach | Impact | Confidence | Data_Readiness | Effort | Risk | AI-RICE Score | Norm_Score |
# Confidence and Data_Readiness stored as integers 0-100 (e.g. "70%").

semantic_errors=0

while IFS= read -r line; do
  # Skip blank lines, header row, separator row
  [[ -z "$line" ]] && continue
  [[ "$line" =~ ^\|[[:space:]]*[-:]+[[:space:]]*\| ]] && continue
  [[ "$line" =~ Reach ]] && continue

  # Extract columns (strip leading/trailing spaces and link syntax)
  raw_reach=$(echo "$line"    | awk -F'|' '{print $3}' | sed 's/\[.*\]([^)]*)/\0/;s/\[//;s/\]([^)]*)//;s/[[:space:]]//g')
  raw_impact=$(echo "$line"   | awk -F'|' '{print $4}' | tr -d ' ')
  raw_conf=$(echo "$line"     | awk -F'|' '{print $5}' | tr -d ' %')
  raw_dr=$(echo "$line"       | awk -F'|' '{print $6}' | tr -d ' %')
  raw_effort=$(echo "$line"   | awk -F'|' '{print $7}' | tr -d ' ')
  raw_risk=$(echo "$line"     | awk -F'|' '{print $8}' | tr -d ' ')
  stored_score=$(echo "$line" | awk -F'|' '{print $9}' | tr -d ' ')

  # Skip rows where columns are not all numeric (e.g. template placeholders)
  for val in "$raw_reach" "$raw_impact" "$raw_conf" "$raw_dr" "$raw_effort" "$raw_risk" "$stored_score"; do
    if ! echo "$val" | grep -qE '^[0-9]+\.?[0-9]*$'; then
      continue 2
    fi
  done

  # Validate ranges
  if ! awk -v c="$raw_conf" 'BEGIN { exit (c >= 0 && c <= 100) ? 0 : 1 }'; then
    echo "Error: CONFIDENCE out of range (0-100): $raw_conf in row: $line"
    semantic_errors=$((semantic_errors + 1))
    continue
  fi
  if ! awk -v dr="$raw_dr" 'BEGIN { exit (dr >= 0 && dr <= 100) ? 0 : 1 }'; then
    echo "Error: DATA_READINESS out of range (0-100): $raw_dr in row: $line"
    semantic_errors=$((semantic_errors + 1))
    continue
  fi
  if ! awk -v r="$raw_risk" 'BEGIN { exit (r >= 1 && r <= 10) ? 0 : 1 }'; then
    echo "Error: RISK out of range (1-10): $raw_risk in row: $line"
    semantic_errors=$((semantic_errors + 1))
    continue
  fi
  if ! awk -v e="$raw_effort" 'BEGIN { exit (e > 0) ? 0 : 1 }'; then
    echo "Error: EFFORT must be positive: $raw_effort in row: $line"
    semantic_errors=$((semantic_errors + 1))
    continue
  fi

  # Verify formula: expected = (R * I * C * DR) / (E * Risk)
  result=$(awk -v r="$raw_reach" -v i="$raw_impact" -v c="$raw_conf" \
    -v dr="$raw_dr" -v e="$raw_effort" -v risk="$raw_risk" -v stored="$stored_score" \
    'BEGIN {
      expected = (r * i * c * dr) / (e * risk)
      diff = expected - stored
      if (diff < 0) diff = -diff
      if (diff > 0.5) {
        printf "MISMATCH: expected=%.2f stored=%s\n", expected, stored
      } else {
        print "OK"
      }
    }')

  if [[ "$result" != "OK" ]]; then
    echo "Error: AI-RICE formula $result for row (Reach=$raw_reach Impact=$raw_impact Conf=$raw_conf% DR=$raw_dr% Effort=$raw_effort Risk=$raw_risk)"
    semantic_errors=$((semantic_errors + 1))
  fi
done < <(grep "^\|" "$FILE_PATH" | tail -n +3)

if [ "$semantic_errors" -gt 0 ]; then
  if [ -x "$STATE_LOG" ]; then
    "$STATE_LOG" "select" "Framework-Driven Development" "AI-RICE semantic validation failed ($semantic_errors errors)" "high" "validate-airice"
  fi
  exit 1
fi

echo "AI-RICE validation passed"
