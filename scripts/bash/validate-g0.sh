#!/usr/bin/env bash
set -euo pipefail

FILE_PATH="${1:-.spec-kit/vision_brief.md}"
STATE_LOG="scripts/bash/state-log-violation.sh"

log_violation() {
  local message="$1"
  local severity="${2:-high}"
  if [ -x "$STATE_LOG" ]; then
    "$STATE_LOG" "validate" "Framework-Driven Development" "$message" "$severity" "validate-g0"
  fi
}

fail() {
  local message="$1"
  local severity="${2:-high}"
  echo "Error: $message"
  log_violation "$message" "$severity"
  exit 1
}

if [ ! -f "$FILE_PATH" ]; then
  fail "vision_brief.md not found at $FILE_PATH" "critical"
fi

required_sections=(
  "One-Liner"
  "Problem Statement"
  "Solution Approach"
  "Success Criteria"
  "Key Assumptions"
  "Data & Model Strategy"
  "Constraints & Risks"
)

for section in "${required_sections[@]}"; do
  if ! rg -q "^## ${section}" "$FILE_PATH"; then
    fail "Missing section: $section"
  fi
done

missing_refs=()
for section in "${required_sections[@]}"; do
  if ! awk -v header="## ${section}" '
    $0 ~ "^" header {in_section=1; found=0; next}
    /^## / { if (in_section && !found) exit 1; in_section=0 }
    in_section && /Canvas References/ {found=1}
    END { if (in_section && !found) exit 1 }
  ' "$FILE_PATH"; then
    missing_refs+=("$section")
  fi
done

if [ "${#missing_refs[@]}" -gt 0 ]; then
  fail "Missing Canvas References in sections: ${missing_refs[*]}"
fi

if rg -q "\\[PLACEHOLDER\\]" "$FILE_PATH"; then
  fail "Found [PLACEHOLDER] tokens in vision_brief"
fi

if ! rg -i -q "When .*I want .*so I can" "$FILE_PATH"; then
  fail "Job statement missing When/I want/So I can format"
fi

assumption_count=$(awk '
  BEGIN{in_section=0}
  /^## Key Assumptions/ {in_section=1; next}
  /^## / {in_section=0}
  in_section && /^\|/ {
    if ($0 ~ /^\|[ -]+\|/) next
    if ($0 ~ /^\| *Assumption *\|/) next
    count++
  }
  END{print count+0}
' "$FILE_PATH")
if [ "$assumption_count" -lt 3 ]; then
  fail "Expected at least 3 assumptions, found $assumption_count"
fi

metric_count=$(awk '
  BEGIN{in_section=0}
  /^## Success Criteria/ {in_section=1; next}
  /^## / {in_section=0}
  in_section && ($0 ~ /^[0-9]+\./ || $0 ~ /^- /) {count++}
  END{print count+0}
' "$FILE_PATH")
if [ "$metric_count" -lt 3 ]; then
  fail "Expected at least 3 success metrics, found $metric_count"
fi

data_source_count=$(awk '
  BEGIN{in_section=0; sub_section=0}
  /^## Data & Model Strategy/ {in_section=1; sub_section=0; next}
  /^## / {in_section=0; sub_section=0}
  in_section && /^\*\*Data Requirements\*\*/ {sub_section=1; next}
  in_section && sub_section && /^\*\*/ {sub_section=0}
  in_section && sub_section && /^- / {count++}
  END{print count+0}
' "$FILE_PATH")
if [ "$data_source_count" -lt 1 ]; then
  fail "Expected at least 1 data source, found $data_source_count"
fi

# Count words in Model Approach subsection
# Must read all lines until next ** header to handle multi-line paragraphs
model_word_count=$(awk '
  BEGIN{in_section=0; sub_section=0}
  # Enter Data & Model Strategy section
  /^## Data & Model Strategy/ {in_section=1; sub_section=0; next}
  # Exit on next main section header
  /^## / {in_section=0; sub_section=0}
  # Found Model Approach subsection header
  in_section && /^\*\*Model Approach\*\*/ {
    sub_section=1
    # Count words on same line as header (if any)
    line=$0
    sub(/^\*\*Model Approach\*\*:? ?/, "", line)
    if (length(line) > 0) {
      n=split(line, words, /[[:space:]]+/)
      count+=n
    }
    next
  }
  # Stop counting when we hit the next ** subsection header (e.g., **Evaluation**)
  in_section && sub_section && /^\*\*/ {sub_section=0}
  # Count words on all lines in the Model Approach subsection
  in_section && sub_section {
    n=split($0, words, /[[:space:]]+/)
    count+=n
  }
  END{print count+0}
' "$FILE_PATH")
if [ "$model_word_count" -lt 50 ]; then
  fail "Model approach must be at least 50 words, found $model_word_count"
fi

echo "Gate G0 automated checks passed"
