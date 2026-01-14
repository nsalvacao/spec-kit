#!/usr/bin/env bash
set -euo pipefail

STATE_DIR=".spec-kit"
STATE_FILE="$STATE_DIR/state.yaml"

command -v yq >/dev/null 2>&1 || { echo "Error: yq not found. Install: brew install yq || sudo apt install yq"; exit 1; }

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
  yq eval ".artifacts.ideas_backlog = \"$ideas_backlog\"" "$STATE_FILE" > "$STATE_DIR/.state.yaml.tmp" && mv "$STATE_DIR/.state.yaml.tmp" "$STATE_FILE"
fi
if [ -f "$idea_selection" ]; then
  yq eval ".artifacts.idea_selection = \"$idea_selection\"" "$STATE_FILE" > "$STATE_DIR/.state.yaml.tmp" && mv "$STATE_DIR/.state.yaml.tmp" "$STATE_FILE"
fi
if [ -f "$ai_vision_canvas" ]; then
  yq eval ".artifacts.ai_vision_canvas = \"$ai_vision_canvas\"" "$STATE_FILE" > "$STATE_DIR/.state.yaml.tmp" && mv "$STATE_DIR/.state.yaml.tmp" "$STATE_FILE"
fi
if [ -f "$vision_brief" ]; then
  yq eval ".artifacts.vision_brief = \"$vision_brief\"" "$STATE_FILE" > "$STATE_DIR/.state.yaml.tmp" && mv "$STATE_DIR/.state.yaml.tmp" "$STATE_FILE"
fi
if [ -f "$g0_report" ]; then
  yq eval ".artifacts.g0_validation_report = \"$g0_report\"" "$STATE_FILE" > "$STATE_DIR/.state.yaml.tmp" && mv "$STATE_DIR/.state.yaml.tmp" "$STATE_FILE"
fi

if [ "${#phases_completed[@]}" -gt 0 ]; then
  phases_json="["
  for phase in "${phases_completed[@]}"; do
    phases_json="${phases_json}\"${phase}\","
  done
  phases_json="${phases_json%,}]"
  yq eval ".phases_completed = $phases_json | .current_phase = \"$current_phase\"" "$STATE_FILE" > "$STATE_DIR/.state.yaml.tmp" && mv "$STATE_DIR/.state.yaml.tmp" "$STATE_FILE"
fi

echo "state.yaml reconstructed"
