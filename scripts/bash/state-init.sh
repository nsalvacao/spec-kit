#!/usr/bin/env bash
set -euo pipefail

STATE_DIR=".spec-kit"
STATE_FILE="$STATE_DIR/state.yaml"

mkdir -p "$STATE_DIR"

if [ ! -f "$STATE_FILE" ]; then
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
  echo "state.yaml initialized"
else
  echo "state.yaml already exists"
fi
