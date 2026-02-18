#!/usr/bin/env bash
# validate-constitution.sh — Constitution validator with Waiver Mechanism
# Requires: Bash 4+ (for associative arrays)
#
# Usage:
#   validate-constitution.sh [FILE_PATH] [--waive CRITERION_ID "justification"] [--report REPORT_PATH]
#
# Examples:
#   validate-constitution.sh
#   validate-constitution.sh .specify/constitution.md
#   validate-constitution.sh .specify/constitution.md --waive Q1 "Phase 0 not used; principles from README"
#   validate-constitution.sh --waive P1 "justification" --report .specify/constitution-validation.md
#
# Automated checks (A1-A8) are non-waivable and always block on failure.
# Manual checks (Q1-Q4, P1-P2) may be waived with a justification.
set -eo pipefail

SCRIPT_DIR="$(CDPATH="" cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FILE_PATH=".specify/constitution.md"
REPORT_PATH=""
STATE_LOG="$SCRIPT_DIR/state-log-violation.sh"
declare -A WAIVERS=()  # WAIVERS[CRITERION_ID]="justification"

# Check required binaries
for _bin in rg awk wc; do
  if ! command -v "$_bin" &>/dev/null; then
    echo "Error: required binary '$_bin' not found. Install it and retry." >&2
    exit 2
  fi
done

# Parse arguments
while [[ $# -gt 0 ]]; do
  case "$1" in
    --waive)
      CRITERION_ID="${2:?--waive requires CRITERION_ID}"
      JUSTIFICATION="${3:?--waive requires justification}"
      WAIVERS["$CRITERION_ID"]="$JUSTIFICATION"
      shift 3
      ;;
    --report)
      REPORT_PATH="${2:?--report requires a file path}"
      shift 2
      ;;
    -*)
      echo "Unknown option: $1" >&2
      exit 1
      ;;
    *)
      FILE_PATH="$1"
      shift
      ;;
  esac
done

# Validate that file paths stay within the project directory
_project_dir=$(realpath .)
if [ -e "$FILE_PATH" ] && [[ "$(realpath "$FILE_PATH")" != "$_project_dir"* ]]; then
  echo "Error: FILE_PATH '$FILE_PATH' is outside the project directory." >&2
  exit 1
fi
if [ -n "$REPORT_PATH" ] && [ -e "$REPORT_PATH" ] && [[ "$(realpath "$REPORT_PATH")" != "$_project_dir"* ]]; then
  echo "Error: REPORT_PATH '$REPORT_PATH' is outside the project directory." >&2
  exit 1
fi

log_violation() {
  local message="$1"
  local severity="${2:-high}"
  if [ -x "$STATE_LOG" ]; then
    "$STATE_LOG" "validate" "Framework-Driven Development" "$message" "$severity" "validate-constitution"
  fi
}

fail_auto() {
  local criterion="$1"
  local message="$2"
  echo "FAIL [${criterion}] ${message}" >&2
  log_violation "$message" "critical"
  exit 1
}

check_manual() {
  local criterion="$1"
  local label="$2"
  local passed="$3"
  local detail="$4"

  if [ "$passed" = "true" ]; then
    echo "PASS [${criterion}] ${label}"
    return 0
  fi

  if [ -n "${WAIVERS[$criterion]+_}" ]; then
    echo "WAIVED [${criterion}] ${label}"
    echo "  Justification: ${WAIVERS[$criterion]}"
    return 0
  fi

  echo "WARN [${criterion}] ${label}: ${detail}"
  return 1
}

# ──────────────────────────────────────────────────────────────
# Automated checks (A1-A8) — non-waivable, always block on failure
# ──────────────────────────────────────────────────────────────

echo "=== Automated Checks ==="

# A1: File exists
if [ ! -f "$FILE_PATH" ]; then
  fail_auto "A1" "Constitution file not found at '$FILE_PATH'"
fi
echo "PASS [A1] Constitution file exists"

# A2: File not empty (>= 20 lines expected for a real constitution)
line_count=$(wc -l < "$FILE_PATH")
if [ "$line_count" -lt 20 ]; then
  fail_auto "A2" "Constitution file too short ($line_count lines); expected >= 20"
fi
echo "PASS [A2] File has $line_count lines (>= 20)"

# A3: Section '## Core Principles' present
if ! rg -q "^## Core Principles" "$FILE_PATH" 2>/dev/null; then
  fail_auto "A3" "Missing required section: '## Core Principles'"
fi
echo "PASS [A3] Section ## Core Principles present"

# A4: Section '## Governance' present
if ! rg -q "^## Governance" "$FILE_PATH" 2>/dev/null; then
  fail_auto "A4" "Missing required section: '## Governance'"
fi
echo "PASS [A4] Section ## Governance present"

# A5: Metadata line present (**Version**: ... | **Ratified**: ... | **Last Amended**: ...)
# Template format uses **Bold**: value, so search for the bold marker pattern
if ! rg -q "Version\*\*:" "$FILE_PATH" 2>/dev/null; then
  fail_auto "A5" "Missing metadata '**Version**:' line in constitution"
fi
if ! rg -q "Ratified\*\*:" "$FILE_PATH" 2>/dev/null; then
  fail_auto "A5" "Missing metadata '**Ratified**:' date in constitution"
fi
echo "PASS [A5] Metadata (**Version**/**Ratified**) present"

# A6: Unfilled placeholders still present
# These tokens indicate the template was not properly filled out
unfilled_tokens=(
  "\\[PROJECT_NAME\\]"
  "\\[PRINCIPLE_[0-9]_NAME\\]"
  "\\[PRINCIPLE_[0-9]_DESCRIPTION\\]"
  "\\[SECTION_[0-9]_NAME\\]"
  "\\[SECTION_[0-9]_CONTENT\\]"
  "\\[GOVERNANCE_RULES\\]"
  "\\[CONSTITUTION_VERSION\\]"
  "\\[RATIFICATION_DATE\\]"
  "\\[LAST_AMENDED_DATE\\]"
)
for token in "${unfilled_tokens[@]}"; do
  if rg -q "$token" "$FILE_PATH" 2>/dev/null; then
    fail_auto "A6" "Unfilled template placeholder found: ${token//\\/}"
  fi
done
echo "PASS [A6] No unfilled template placeholders"

# A7: At least 3 principles defined (### sub-headers inside Core Principles section)
principle_count=$(awk '
  /^## Core Principles/ { in_section=1; next }
  /^## / && in_section  { in_section=0 }
  in_section && /^### / { count++ }
  END { print count+0 }
' "$FILE_PATH")
if [ "$principle_count" -lt 3 ]; then
  fail_auto "A7" "Too few principles defined ($principle_count); expected >= 3 (### sub-headers in Core Principles)"
fi
echo "PASS [A7] $principle_count principles defined (>= 3)"

# A8: Governance section has substantive content (not just the placeholder comment)
governance_lines=$(awk '
  /^## Governance/ { in_section=1; next }
  /^## /           { in_section=0 }
  in_section && /^[^#<]/ && length($0) > 5 { count++ }
  END { print count+0 }
' "$FILE_PATH")
if [ "$governance_lines" -lt 1 ]; then
  fail_auto "A8" "Governance section has no substantive content (only comments/headers)"
fi
echo "PASS [A8] Governance has $governance_lines substantive line(s)"

echo ""
echo "=== Manual Checks ==="

manual_warns=0

# Q1: Phase 0 integration block removed (template placeholder comment gone)
# The template contains a large HTML comment block starting with "PHASE 0 INTEGRATION CHECK"
# A properly filled constitution should have removed it and replaced with real principles
has_phase0_block="false"
if rg -q "PHASE 0 INTEGRATION CHECK" "$FILE_PATH" 2>/dev/null; then
  has_phase0_block="true"
fi
# Pass if the block is gone (false = not found)
q1_passed="false"
[ "$has_phase0_block" = "false" ] && q1_passed="true"
check_manual "Q1" "Phase 0 integration comment block removed" "$q1_passed" \
  "Template comment block 'PHASE 0 INTEGRATION CHECK' still present; derive principles from Phase 0 artifacts and remove the comment" || manual_warns=$((manual_warns+1))

# Q2: Each principle has substantive description (not just a one-liner <= 20 chars)
short_principles=$(awk '
  function check_prev() {
    if (in_principle && desc_len <= 20) count++
  }
  /^## Core Principles/ { in_section=1; in_principle=0; next }
  /^## / && in_section   { check_prev(); in_section=0; in_principle=0 }
  in_section && /^### /  { check_prev(); in_principle=1; desc_len=0; next }
  in_section && in_principle && /^[^#<]/ && length($0) > 3 {
    desc_len += length($0)
  }
  END {
    if (in_section) check_prev()
    print count+0
  }
' "$FILE_PATH")
q2_passed="false"
[ "$short_principles" -eq 0 ] && q2_passed="true"
check_manual "Q2" "All principles have substantive descriptions (> 20 chars)" "$q2_passed" \
  "$short_principles principle(s) have very short or missing descriptions" || manual_warns=$((manual_warns+1))

# Q3: Governance section references amendment or compliance process
has_governance_process="false"
if rg -i -q "(amendment|amend|compliance|supersede|ratif|review process|update process)" "$FILE_PATH" 2>/dev/null; then
  has_governance_process="true"
fi
check_manual "Q3" "Governance includes amendment/compliance process" "$has_governance_process" \
  "No amendment or compliance process found in Governance section" || manual_warns=$((manual_warns+1))

# Q4: At least one additional section beyond Core Principles and Governance
extra_sections=$(awk '
  /^## Core Principles/ || /^## Governance/ { skip=1; next }
  skip && /^## /        { skip=0 }
  !skip && /^## /       { count++ }
  END { print count+0 }
' "$FILE_PATH")
q4_passed="false"
[ "$extra_sections" -ge 1 ] && q4_passed="true"
check_manual "Q4" "At least one additional section (e.g. Constraints, Workflow, Quality Gates)" "$q4_passed" \
  "Only Core Principles and Governance found; add at least one domain-specific section" || manual_warns=$((manual_warns+1))

# P1: Phase 0 artifacts referenced (or Phase 0 was not used, documented with waiver)
has_phase0_ref="false"
if rg -i -q "(\.spec-kit/|ai_vision_canvas|ideas_backlog|idea_selection|g0_validation|vision_brief)" "$FILE_PATH" 2>/dev/null; then
  has_phase0_ref="true"
fi
check_manual "P1" "Phase 0 artifacts referenced in constitution" "$has_phase0_ref" \
  "No references to .spec-kit/ Phase 0 artifacts found; if Phase 0 was not used, waive with justification" || manual_warns=$((manual_warns+1))

# P2: Principles relate to AI/ML concerns if canvas references AI task (C12)
# Only applies if the project canvas mentions AI Task
has_canvas="false"
canvas_file=".spec-kit/ai_vision_canvas.md"
if [ -f "$canvas_file" ] && rg -i -q "(C12|AI Task|machine learning|model)" "$canvas_file" 2>/dev/null; then
  has_canvas="true"
fi
if [ "$has_canvas" = "true" ]; then
  has_ai_principles="false"
  if rg -i -q "(model|inference|ai|ml|data|accuracy|safety|fairness|bias)" "$FILE_PATH" 2>/dev/null; then
    has_ai_principles="true"
  fi
  check_manual "P2" "AI/ML principles present (canvas declares AI Task C12)" "$has_ai_principles" \
    "Canvas declares AI task but constitution has no AI/ML principles" || manual_warns=$((manual_warns+1))
else
  echo "SKIP [P2] AI/ML principles check (no AI canvas or C12 reference found)"
fi

# ──────────────────────────────────────────────────────────────
# Waiver registration in report
# ──────────────────────────────────────────────────────────────

if [ ${#WAIVERS[@]} -gt 0 ] && [ -n "$REPORT_PATH" ] && [ -f "$REPORT_PATH" ]; then
  echo ""
  echo "=== Registering Waivers in Report ==="
  waiver_block=""
  for crit in "${!WAIVERS[@]}"; do
    waiver_block+="| ${crit} | ${WAIVERS[$crit]} |"$'\n'
  done

  if rg -q "^## Waivers" "$REPORT_PATH"; then
    # Idempotent: remove any previously inserted waiver table rows, then insert fresh ones
    WAIVER_BLOCK="$waiver_block" awk '
      /^## Waivers/ { print; print ""; printf "%s", ENVIRON["WAIVER_BLOCK"]; in_waivers=1; next }
      in_waivers && /^\| / { next }
      { in_waivers=0; print }
    ' "$REPORT_PATH" > "${REPORT_PATH}.tmp" && mv "${REPORT_PATH}.tmp" "$REPORT_PATH"
    echo "Waivers registered in $REPORT_PATH"
  fi
fi

# ──────────────────────────────────────────────────────────────
# Final result
# ──────────────────────────────────────────────────────────────

echo ""

if [ "$manual_warns" -gt 0 ]; then
  echo "RESULT: FAIL — $manual_warns manual check(s) unresolved"
  echo "  → Provide --waive CRITERION_ID \"justification\" for each unresolved check"
  log_violation "$manual_warns manual checks failed in constitution validation" "high"
  exit 1
elif [ "${#WAIVERS[@]}" -gt 0 ]; then
  echo "RESULT: PASS WITH WAIVER — all automated checks passed; ${#WAIVERS[@]} waiver(s) applied"
else
  echo "RESULT: PASS — all checks passed"
fi
