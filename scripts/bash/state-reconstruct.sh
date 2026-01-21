#!/usr/bin/env bash
set -euo pipefail

STATE_DIR=".spec-kit"
STATE_FILE="$STATE_DIR/state.yaml"
SCRIPT_DIR="$(CDPATH="" cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_SCRIPT="$SCRIPT_DIR/../python/state-update.py"

command -v python3 >/dev/null 2>&1 || { echo "Error: python3 not found. Please install Python 3"; exit 1; }

mkdir -p "$STATE_DIR"

ideas_backlog="$STATE_DIR/ideas_backlog.md"
idea_selection="$STATE_DIR/idea_selection.md"
ai_vision_canvas="$STATE_DIR/ai_vision_canvas.md"
vision_brief="$STATE_DIR/vision_brief.md"
g0_report="$STATE_DIR/approvals/g0-validation-report.md"

phases_completed=()
current_phase="ideate"

if [ -f "$ideas_backlog" ]; then
  phases_completed+=("ideate")
  current_phase="select"
fi
if [ -f "$idea_selection" ]; then
  phases_completed+=("select")
  current_phase="structure"
fi
if [ -f "$ai_vision_canvas" ] && [ -f "$vision_brief" ]; then
  phases_completed+=("structure")
  current_phase="validate"
fi
if [ -f "$g0_report" ]; then
  phases_completed+=("validate")
  current_phase="validate"
fi

cat > "$STATE_FILE" <<'EOF'
workflow_version: "1.0"
current_phase: ideate
phases_completed: []
phases_in_progress: []
artifacts:
  ideas_backlog: null
  idea_selection: null
  ai_vision_canvas: null
  vision_brief: null
  g0_validation_report: null
profile: ai-system
violations: []
EOF

if [ -f "$ideas_backlog" ]; then
  python3 "$PYTHON_SCRIPT" --file "$STATE_FILE" --operation set-value --key artifacts.ideas_backlog --value "$ideas_backlog"
fi
if [ -f "$idea_selection" ]; then
  python3 "$PYTHON_SCRIPT" --file "$STATE_FILE" --operation set-value --key artifacts.idea_selection --value "$idea_selection"
fi
if [ -f "$ai_vision_canvas" ]; then
  python3 "$PYTHON_SCRIPT" --file "$STATE_FILE" --operation set-value --key artifacts.ai_vision_canvas --value "$ai_vision_canvas"
fi
if [ -f "$vision_brief" ]; then
  python3 "$PYTHON_SCRIPT" --file "$STATE_FILE" --operation set-value --key artifacts.vision_brief --value "$vision_brief"
fi
if [ -f "$g0_report" ]; then
  python3 "$PYTHON_SCRIPT" --file "$STATE_FILE" --operation set-value --key artifacts.g0_validation_report --value "$g0_report"
fi

if [ "${#phases_completed[@]}" -gt 0 ]; then
  # Build JSON array for phases_completed
  phases_json="["
  for phase in "${phases_completed[@]}"; do
    phases_json="${phases_json}\"${phase}\","
  done
  phases_json="${phases_json%,}]"
  
  # Set both phases_completed and current_phase using set-multiple
  python3 "$PYTHON_SCRIPT" --file "$STATE_FILE" --operation set-multiple --json-data "{\"phases_completed\": $phases_json, \"current_phase\": \"$current_phase\"}"
fi

echo "state.yaml reconstructed"
