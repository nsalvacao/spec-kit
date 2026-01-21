#!/usr/bin/env bash
set -euo pipefail

FILE_PATH="${1:-.spec-kit/ai_vision_canvas.md}"
STATE_LOG="scripts/bash/state-log-violation.sh"

if [ ! -f "$FILE_PATH" ]; then
  echo "Error: ai_vision_canvas not found at $FILE_PATH"
  if [ -x "$STATE_LOG" ]; then
    "$STATE_LOG" "structure" "Framework-Driven Development" "ai_vision_canvas.md missing" "critical" "validate-canvas"
  fi
  exit 1
fi

required_sections=(
  "### 1. Job Statement (When/Want/So)"
  "### 2. Job Executor"
  "### 3. Job Context"
  "### 4. Desired Outcomes"
  "### 5. Current Solution Pains"
  "### 6. Top 3 Problems"
  "### 7. Solution (High-Level)"
  "### 8. Key Assumptions (Critical, Unvalidated)"
  "### 9. Validation Methods (Build-Measure-Learn)"
  "### 10. Key Metrics (Success Criteria)"
  "### 11. Cost Structure (Budget Constraints)"
  "### 12. AI Task"
  "### 13. Data Requirements"
  "### 14. Model Approach"
  "### 15. Evaluation Strategy"
  "### 16. Safety & Risk"
  "### 17. Constraints"
  "### 18. Infrastructure (High-Level)"
)

missing=()
for section in "${required_sections[@]}"; do
  if ! rg -qF "$section" "$FILE_PATH"; then
    missing+=("$section")
  fi
done

if [ "${#missing[@]}" -gt 0 ]; then
  echo "Error: Missing canvas sections: ${missing[*]}"
  if [ -x "$STATE_LOG" ]; then
    "$STATE_LOG" "structure" "Framework-Driven Development" "Missing canvas sections: ${missing[*]}" "high" "validate-canvas"
  fi
  exit 1
fi

section_count=$(rg -c "^### [0-9]+\\." "$FILE_PATH" || true)
if [ "$section_count" -lt 18 ]; then
  echo "Error: Expected 18 canvas components, found $section_count"
  if [ -x "$STATE_LOG" ]; then
    "$STATE_LOG" "structure" "Framework-Driven Development" "Canvas components missing: $section_count/18" "high" "validate-canvas"
  fi
  exit 1
fi

if ! rg -i -q "When .*I want .*so I can" "$FILE_PATH"; then
  echo "Error: Job statement missing When/I want/So I can format"
  if [ -x "$STATE_LOG" ]; then
    "$STATE_LOG" "structure" "Framework-Driven Development" "Job statement missing When/I want/So I can format" "high" "validate-canvas"
  fi
  exit 1
fi

if rg -q "\\[PLACEHOLDER\\]" "$FILE_PATH"; then
  echo "Error: Found [PLACEHOLDER] tokens in canvas"
  if [ -x "$STATE_LOG" ]; then
    "$STATE_LOG" "structure" "Framework-Driven Development" "Found [PLACEHOLDER] tokens in canvas" "high" "validate-canvas"
  fi
  exit 1
fi

echo "Vision canvas validation passed"
