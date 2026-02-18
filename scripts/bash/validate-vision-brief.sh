#!/usr/bin/env bash
# validate-vision-brief.sh — Vision Brief validator with Waiver Mechanism
#
# Usage:
#   validate-vision-brief.sh [FILE_PATH] [--waive CRITERION_ID "justification"] [--report REPORT_PATH]
#
# Examples:
#   validate-vision-brief.sh
#   validate-vision-brief.sh .spec-kit/vision_brief.md
#   validate-vision-brief.sh .spec-kit/vision_brief.md --waive Q2 "Metrics not finalised yet"
#   validate-vision-brief.sh --waive Q2 "justification" --waive AI4 "budget TBD" --report .spec-kit/g0_validation_report.md
#
# Automated checks (A1-A8) are non-waivable and always block on failure.
# Manual checks (Q1-Q5, AI1-AI4, C1-C3) may be waived with a justification.
set -eo pipefail

SCRIPT_DIR="$(CDPATH="" cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FILE_PATH=".spec-kit/vision_brief.md"
REPORT_PATH=""
STATE_LOG="$SCRIPT_DIR/state-log-violation.sh"
declare -A WAIVERS=()  # WAIVERS[CRITERION_ID]="justification"

# Check required binaries
for _bin in rg awk; do
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

log_violation() {
  local message="$1"
  local severity="${2:-high}"
  if [ -x "$STATE_LOG" ]; then
    "$STATE_LOG" "validate" "Framework-Driven Development" "$message" "$severity" "validate-vision-brief"
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

  if [[ -v WAIVERS["$criterion"] ]]; then
    echo "WAIVED [${criterion}] ${label} — ${WAIVERS[$criterion]}"
    return 0
  fi

  echo "WARN [${criterion}] ${label}: ${detail}"
  echo "  → To waive: --waive ${criterion} \"<justification>\""
  return 1
}

# ──────────────────────────────────────────────────────────────
# Automated Checks (non-waivable)
# ──────────────────────────────────────────────────────────────

echo "=== Automated Checks (non-waivable) ==="

# A1: File exists
[ -f "$FILE_PATH" ] || fail_auto "A1" "vision_brief.md not found at $FILE_PATH"
echo "PASS [A1] vision_brief.md exists"

# A2: All 7 required sections present
required_sections=(
  "One-Liner"
  "Problem Statement"
  "Solution Approach"
  "Success Criteria"
  "Key Assumptions"
  "Data & Model Strategy"
  "Constraints & Risks"
)
missing_sections=()
for section in "${required_sections[@]}"; do
  if ! rg -q "^## ${section}" "$FILE_PATH"; then
    missing_sections+=("$section")
  fi
done
if [ "${#missing_sections[@]}" -gt 0 ]; then
  fail_auto "A2" "Missing sections: ${missing_sections[*]}"
fi
echo "PASS [A2] All 7 sections present"

# A3: No [PLACEHOLDER] tokens
if rg -q "\[PLACEHOLDER\]" "$FILE_PATH"; then
  fail_auto "A3" "Found [PLACEHOLDER] tokens in vision_brief"
fi
echo "PASS [A3] No placeholder tokens"

# A4: Job statement format
if ! rg -i -q "When .*I want .*so I can" "$FILE_PATH"; then
  fail_auto "A4" "Job statement missing 'When/I want/So I can' format in Problem Statement"
fi
echo "PASS [A4] Job statement format valid"

# A5: ≥3 assumptions
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
  fail_auto "A5" "Expected ≥3 assumptions, found $assumption_count"
fi
echo "PASS [A5] ≥3 assumptions (found $assumption_count)"

# A6: ≥3 metrics
metric_count=$(awk '
  BEGIN{in_section=0}
  /^## Success Criteria/ {in_section=1; next}
  /^## / {in_section=0}
  in_section && ($0 ~ /^[0-9]+\./ || $0 ~ /^- /) {count++}
  END{print count+0}
' "$FILE_PATH")
if [ "$metric_count" -lt 3 ]; then
  fail_auto "A6" "Expected ≥3 metrics, found $metric_count"
fi
echo "PASS [A6] ≥3 metrics (found $metric_count)"

# A7: ≥1 data source
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
  fail_auto "A7" "Expected ≥1 data source, found $data_source_count"
fi
echo "PASS [A7] ≥1 data source (found $data_source_count)"

# A8: Model approach ≥50 words
model_word_count=$(awk '
  BEGIN{in_section=0; sub_section=0}
  /^## Data & Model Strategy/ {in_section=1; sub_section=0; next}
  /^## / {in_section=0; sub_section=0}
  in_section && /^\*\*Model Approach\*\*/ {
    sub_section=1
    line=$0; sub(/^\*\*Model Approach\*\*:? ?/, "", line)
    if (length(line) > 0) { n=split(line, words, /[[:space:]]+/); count+=n }
    next
  }
  in_section && sub_section && /^\*\*/ {sub_section=0}
  in_section && sub_section && length($0) > 0 {
    n=split($0, words, /[[:space:]]+/); count+=n
  }
  END{print count+0}
' "$FILE_PATH")
if [ "$model_word_count" -lt 50 ]; then
  fail_auto "A8" "Model approach must be ≥50 words, found $model_word_count"
fi
echo "PASS [A8] Model approach ≥50 words (found $model_word_count)"

echo ""
echo "=== Manual Checks — Quality (waivable) ==="

manual_warns=0

# Q1: Assumptions have validation methods
has_validation_methods="false"
if awk '
  BEGIN{in_section=0}
  /^## Key Assumptions/ {in_section=1; next}
  /^## / {in_section=0}
  in_section && /Validation Method/ {found=1; exit}
  END{if (found) exit 0; else exit 1}
' "$FILE_PATH" 2>/dev/null; then has_validation_methods="true"; fi
check_manual "Q1" "Assumptions have validation methods" "$has_validation_methods" \
  "Assumption table missing Validation Method column" || manual_warns=$((manual_warns+1))

# Q2: Metrics are SMART (look for time-bound indicators)
has_smart_metrics="false"
if rg -i -q "(by |within |Q[0-9]|month|week|year|target:|%|>=|<=|≥|≤)" "$FILE_PATH" 2>/dev/null; then
  has_smart_metrics="true"
fi
check_manual "Q2" "Metrics are SMART" "$has_smart_metrics" \
  "No measurable/time-bound metric indicators found (look for %, ≥, 'by [date]')" || manual_warns=$((manual_warns+1))

# Q3: Data sources concrete (availability %)
has_concrete_sources="false"
if rg -i -q "[0-9]+\s*%" "$FILE_PATH" 2>/dev/null; then has_concrete_sources="true"; fi
check_manual "Q3" "Data sources concrete with availability %" "$has_concrete_sources" \
  "No availability % found in data sources" || manual_warns=$((manual_warns+1))

# Q4: Model rationale present (≥20 words in Model Approach beyond header)
q4_passed="false"
[ "$model_word_count" -ge 20 ] && q4_passed="true"
check_manual "Q4" "Model rationale present" "$q4_passed" \
  "Model Approach section appears too brief for a rationale" || manual_warns=$((manual_warns+1))

# Q5: Risk mitigations defined
has_mitigations="false"
if rg -i -q "(mitigation|mitigate|controls?)" "$FILE_PATH" 2>/dev/null; then
  has_mitigations="true"
fi
check_manual "Q5" "Risk mitigations defined" "$has_mitigations" \
  "No mitigation language found in Constraints & Risks" || manual_warns=$((manual_warns+1))

echo ""
echo "=== Manual Checks — AI-Specific (waivable) ==="

# AI1: Data readiness ≥60%
has_readiness="false"
if rg -q "[6-9][0-9]%|100%" "$FILE_PATH" 2>/dev/null; then has_readiness="true"; fi
check_manual "AI1" "Data readiness ≥60%" "$has_readiness" \
  "No data readiness ≥60% found" || manual_warns=$((manual_warns+1))

# AI2: Evaluation strategy defined
has_eval="false"
if rg -i -q "(evaluation|benchmark|accuracy|precision|recall|F1|BLEU|rouge)" "$FILE_PATH" 2>/dev/null; then
  has_eval="true"
fi
check_manual "AI2" "Evaluation strategy defined" "$has_eval" \
  "No evaluation metrics/benchmarks found" || manual_warns=$((manual_warns+1))

# AI3: Safety assessment complete
has_safety="false"
if rg -i -q "(safety|risk|bias|hallucination|compliance|regulatory)" "$FILE_PATH" 2>/dev/null; then
  has_safety="true"
fi
check_manual "AI3" "Safety assessment complete" "$has_safety" \
  "No safety/risk language found" || manual_warns=$((manual_warns+1))

# AI4: Cost viability aligned
has_cost="false"
if rg -i -q "(budget|cost|viabilit|pricing|inference)" "$FILE_PATH" 2>/dev/null; then
  has_cost="true"
fi
check_manual "AI4" "Cost viability aligned" "$has_cost" \
  "No cost/budget reference found" || manual_warns=$((manual_warns+1))

echo ""
echo "=== Manual Checks — Consistency (waivable) ==="

# C1: Canvas References present in all sections
canvas_refs_ok="false"
all_have_refs=true
for section in "${required_sections[@]}"; do
  if ! awk -v header="## ${section}" '
    $0 ~ "^" header {in_section=1; found=0; next}
    /^## / { if (in_section && !found) exit 1; in_section=0 }
    in_section && /Canvas References/ {found=1}
    END { if (in_section && !found) exit 1 }
  ' "$FILE_PATH" 2>/dev/null; then
    all_have_refs=false
    break
  fi
done
[ "$all_have_refs" = "true" ] && canvas_refs_ok="true"
check_manual "C1" "Canvas References present in all sections" "$canvas_refs_ok" \
  "One or more sections missing 'Canvas References'" || manual_warns=$((manual_warns+1))

# C2: Solution aligned with AI task (both present)
has_alignment="false"
if rg -i -q "(AI Task|canvas.*C12|C12.*canvas)" "$FILE_PATH" 2>/dev/null; then
  has_alignment="true"
fi
check_manual "C2" "Solution aligned with AI task (C12 reference)" "$has_alignment" \
  "No explicit C12 (AI Task) reference found in Solution Approach" || manual_warns=$((manual_warns+1))

# C3: Constraints aligned with model choice
has_constraints_model="false"
if rg -i -q "(latency|constraint.*model|model.*constraint|C17|C14)" "$FILE_PATH" 2>/dev/null; then
  has_constraints_model="true"
fi
check_manual "C3" "Constraints aligned with model choice" "$has_constraints_model" \
  "No explicit constraint-model alignment found" || manual_warns=$((manual_warns+1))

# ──────────────────────────────────────────────────────────────
# Waiver registration
# ──────────────────────────────────────────────────────────────

if [ ${#WAIVERS[@]} -gt 0 ] && [ -n "$REPORT_PATH" ] && [ -f "$REPORT_PATH" ]; then
  echo ""
  echo "=== Registering Waivers in Report ==="
  TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
  waiver_block=""
  waiver_num=1
  for criterion in "${!WAIVERS[@]}"; do
    justification="${WAIVERS[$criterion]}"
    waiver_block+="### Waiver W${waiver_num}: ${criterion}\n"
    waiver_block+="**Justification**: ${justification}\n"
    waiver_block+="**Approved By**: validate-vision-brief.sh (automated waiver registration)\n"
    waiver_block+="**Timestamp**: ${TIMESTAMP}\n\n"
    waiver_num=$((waiver_num+1))
  done

  if rg -q "^## Waivers" "$REPORT_PATH"; then
    # Append waivers after the Waivers section header using ENVIRON to avoid awk -v escape injection
    WAIVER_BLOCK="$waiver_block" awk '
      /^## Waivers/ {print; print ""; printf "%s", ENVIRON["WAIVER_BLOCK"]; next}
      {print}
    ' "$REPORT_PATH" > "${REPORT_PATH}.tmp" && mv "${REPORT_PATH}.tmp" "$REPORT_PATH"
    echo "Waivers registered in $REPORT_PATH"
  else
    echo "Warning: No '## Waivers' section found in $REPORT_PATH — waivers not registered"
  fi
fi

# ──────────────────────────────────────────────────────────────
# Final result
# ──────────────────────────────────────────────────────────────

echo ""

if [ "$manual_warns" -gt 0 ]; then
  echo "RESULT: FAIL — $manual_warns manual check(s) unresolved"
  echo "  → Provide --waive CRITERION_ID \"justification\" for each unresolved check"
  log_violation "$manual_warns manual checks failed in vision_brief validation" "high"
  exit 1
elif [ "${#WAIVERS[@]}" -gt 0 ]; then
  echo "RESULT: PASS WITH WAIVER — all automated checks passed; $waiver_count waiver(s) applied"
else
  echo "RESULT: PASS — all checks passed"
fi
