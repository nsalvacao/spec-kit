#!/usr/bin/env bash
# validate-execution-plan.sh - structural and depth validator for execution-plan.md

set -euo pipefail

if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
  echo "Usage: $(basename "$0") [FILE_PATH]"
  echo ""
  echo "Validate .ideas/execution-plan.md structure and minimum strategic depth."
  echo ""
  echo "Arguments:"
  echo "  FILE_PATH   Path to execution-plan markdown file (default: .ideas/execution-plan.md)"
  echo ""
  echo "Note:"
  echo "  Default path is resolved from the current working directory."
  echo ""
  echo "Validation thresholds:"
  echo "  - No remaining 'TODO:' placeholders"
  echo "  - Minimum 180 lines"
  echo "  - Minimum 4 roadmap phases (### Phase N:)"
  echo "  - Minimum 8 rows in Pre-Mortem Analysis (section 4b)"
  echo "  - Minimum 10 rows in Risk Register (section 5)"
  echo "  - Minimum 5 rows in Contrarian Challenges (section 7)"
  exit 0
fi

for dep in rg awk wc cat; do
  if ! command -v "$dep" >/dev/null 2>&1; then
    echo "Error: required dependency '$dep' is not available in PATH." >&2
    exit 1
  fi
done

FILE_PATH="${1:-.ideas/execution-plan.md}"

if [ ! -f "$FILE_PATH" ]; then
  echo "Error: execution plan document not found at $FILE_PATH" >&2
  exit 1
fi

required_sections=(
  "^## 1\\. Second-Order Thinking & Anticipation Layer$"
  "^### 1\\.1 Second-Order Effects by Initiative$"
  "^### 1\\.2 Failure Modes by Phase$"
  "^### 1\\.3 Competitive Responses$"
  "^### 1\\.4 Timing Risks$"
  "^### 1\\.5 Dependencies & Critical Path$"
  "^## 2\\. Polish & Improvements Before Public Exposure$"
  "^### 2\\.1 Code Quality Audit Checklist$"
  "^### 2\\.2 Documentation Gaps$"
  "^### 2\\.3 README Optimization$"
  "^### 2\\.4 Demo/GIF/Video Needs$"
  "^### 2\\.5 Pre-Launch Evaluation Checkpoint$"
  "^## 3\\. Expected Impacts Matrix$"
  "^## 4\\. Operationalized Roadmap$"
  "^## 4b\\. Pre-Mortem Analysis$"
  "^## 4c\\. Moat Assessment$"
  "^## 5\\. Risk Register$"
  "^## 6\\. Growth & Visibility Strategy$"
  "^## 7\\. Contrarian Challenges$"
  "^## Appendices$"
)

for section in "${required_sections[@]}"; do
  if ! rg -q "$section" -- "$FILE_PATH"; then
    echo "Error: Missing required section matching pattern: $section" >&2
    exit 1
  fi
done

if rg -q "TODO:" -- "$FILE_PATH"; then
  echo "Error: Document still contains TODO placeholders." >&2
  exit 1
fi

line_count=$(wc -l < "$FILE_PATH")
if [ "$line_count" -lt 180 ]; then
  echo "Error: Expected at least 180 lines for minimum strategic depth, found $line_count." >&2
  exit 1
fi

phase_count=$(rg -c '^### Phase [0-9]+:' -- "$FILE_PATH" || true)
if [ "$phase_count" -lt 4 ]; then
  echo "Error: Expected at least 4 roadmap phases, found $phase_count." >&2
  exit 1
fi

# Use `cat --` so leading-hyphen file paths are not treated as awk options.
premortem_rows=$(cat -- "$FILE_PATH" | awk '
  /^## 4b\. Pre-Mortem Analysis/ {in_section=1; next}
  /^## 4c\. / {in_section=0}
  in_section {print}
' | rg '^\|[^|]' | rg -v '^\|[[:space:]]*---' | rg -v '^\|[[:space:]]*#' | wc -l || true)

if [ "$premortem_rows" -lt 8 ]; then
  echo "Error: Expected at least 8 pre-mortem rows, found $premortem_rows." >&2
  exit 1
fi

risk_rows=$(cat -- "$FILE_PATH" | awk '
  /^## 5\. Risk Register/ {in_section=1; next}
  /^## 6\. / {in_section=0}
  in_section {print}
' | rg '^\|[^|]' | rg -v '^\|[[:space:]]*---' | rg -v '^\|[[:space:]]*#' | wc -l || true)

if [ "$risk_rows" -lt 10 ]; then
  echo "Error: Expected at least 10 risk rows, found $risk_rows." >&2
  exit 1
fi

contrarian_rows=$(cat -- "$FILE_PATH" | awk '
  /^## 7\. Contrarian Challenges/ {in_section=1; next}
  /^## Appendices/ {in_section=0}
  in_section {print}
' | rg '^\|[^|]' | rg -v '^\|[[:space:]]*---' | rg -v '^\|[[:space:]]*Assumption[[:space:]]*\|' | wc -l || true)

if [ "$contrarian_rows" -lt 5 ]; then
  echo "Error: Expected at least 5 contrarian challenge rows, found $contrarian_rows." >&2
  exit 1
fi

echo "Execution plan validation passed"
