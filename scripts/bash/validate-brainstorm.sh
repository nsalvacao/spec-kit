#!/usr/bin/env bash
# validate-brainstorm.sh — structural and depth validator for brainstorm-expansion.md

set -euo pipefail

FILE_PATH="${1:-.ideas/brainstorm-expansion.md}"

if [ ! -f "$FILE_PATH" ]; then
  echo "Error: brainstorm document not found at $FILE_PATH" >&2
  exit 1
fi

required_sections=(
  "^## 1\\. What Is the REAL Asset\\?$"
  "^## 2\\. SCAMPER Analysis$"
  "^## 3\\. Divergent Ideation"
  "^## 4\\. Convergent Analysis"
  "^## 5\\. Blue Ocean Strategy$"
  "^## 6\\. TAM/SAM/SOM$"
  "^## 7\\. Jobs-to-be-Done$"
  "^## 8\\. Flywheel$"
  "^## 9\\. One-Line Pitches$"
  "^## 10\\. Honest Weaknesses & Risks$"
  "^## 11\\. Monday Morning Actions$"
)

for section in "${required_sections[@]}"; do
  if ! rg -q "$section" "$FILE_PATH"; then
    echo "Error: Missing required section matching pattern: $section" >&2
    exit 1
  fi
done

if rg -q "TODO:" "$FILE_PATH"; then
  echo "Error: Document still contains TODO placeholders." >&2
  exit 1
fi

line_count=$(wc -l < "$FILE_PATH")
if [ "$line_count" -lt 120 ]; then
  echo "Error: Expected at least 120 lines for minimum strategic depth, found $line_count." >&2
  exit 1
fi

divergent_count=$(awk '
  /^## 3\. Divergent Ideation/ {in_section=1; next}
  /^## 4\. / {in_section=0}
  in_section {print}
' "$FILE_PATH" | rg -c '^[0-9]+\. ' || true)

if [ "$divergent_count" -lt 20 ]; then
  echo "Error: Expected at least 20 divergent ideas, found $divergent_count." >&2
  exit 1
fi

tier_count=$(rg -c '^#### [SA][0-9]+:' "$FILE_PATH" || true)
if [ "$tier_count" -lt 3 ]; then
  echo "Error: Expected at least 3 detailed Tier S/A entries, found $tier_count." >&2
  exit 1
fi

risk_data_rows=$(awk '
  /^## 10\. Honest Weaknesses & Risks/ {in_section=1; next}
  /^## 11\. / {in_section=0}
  in_section {print}
' "$FILE_PATH" | rg '^\|[^|]' | rg -v '^\|[[:space:]]*---' | rg -v '^\|[[:space:]]*Weakness[[:space:]]*\|' | wc -l)

if [ "$risk_data_rows" -lt 5 ]; then
  echo "Error: Expected at least 5 risk rows, found $risk_data_rows." >&2
  exit 1
fi

actions_count=$(awk '
  /^## 11\. Monday Morning Actions/ {in_section=1; next}
  in_section {print}
' "$FILE_PATH" | rg -c '^[0-9]+\. ' || true)

if [ "$actions_count" -lt 5 ]; then
  echo "Error: Expected at least 5 Monday Morning actions, found $actions_count." >&2
  exit 1
fi

echo "Brainstorm validation passed"
