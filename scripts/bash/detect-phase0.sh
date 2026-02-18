#!/usr/bin/env bash
# detect-phase0.sh — Detect if Phase 0 was used in this project
#
# Exit 0 if Phase 0 is detected (ideation, selection, or structure completed)
# Exit 1 if Phase 0 was not used
#
# Detection strategy (Option B with Option A fallback):
#   1. Parse .spec-kit/state.yaml for phases_completed entries
#   2. Fallback: check for non-empty .spec-kit/ideation/ directory
#
# Usage:
#   ./detect-phase0.sh               # silent — use exit code
#   ./detect-phase0.sh --verbose     # print reason to stdout
#   ./detect-phase0.sh --json        # output JSON: {"phase0":true,"method":"state","phases":["ideate"]}

set -euo pipefail

STATE_FILE=".spec-kit/state.yaml"
IDEATION_DIR=".spec-kit/ideation"

VERBOSE=false
JSON=false

for arg in "$@"; do
    case "$arg" in
        --verbose|-v) VERBOSE=true ;;
        --json)       JSON=true ;;
        --help|-h)
            echo "Usage: $(basename "$0") [--verbose] [--json]"
            echo ""
            echo "Detects whether Phase 0 (AI System Ideation) was used in this project."
            echo ""
            echo "Exit codes:"
            echo "  0  Phase 0 detected"
            echo "  1  Phase 0 not detected"
            exit 0
            ;;
    esac
done

# ─── Option B: Parse state.yaml ──────────────────────────────────────────────

if [ -f "$STATE_FILE" ] && command -v python3 >/dev/null 2>&1; then
    result=$(python3 - "$STATE_FILE" 2>/dev/null <<'PYEOF'
import yaml, sys, json

try:
    with open(sys.argv[1], 'r') as f:
        data = yaml.safe_load(f) or {}
except Exception:
    data = {}

phases = data.get('phases_completed', []) or []
phase0_phases = ['ideate', 'ideation', 'selection', 'structure']
found = [p for p in phases if p in phase0_phases]

print(json.dumps({
    "phase0": len(found) > 0,
    "method": "state",
    "phases": found
}))
PYEOF
    ) || result=""

    detected=$(echo "$result" | python3 -c "import json,sys; d=json.load(sys.stdin); print('true' if d['phase0'] else 'false')")
    found_phases=$(echo "$result" | python3 -c "import json,sys; d=json.load(sys.stdin); print(','.join(d['phases']) if d['phases'] else '')")

    if [ "$detected" = "true" ]; then
        if $JSON; then
            echo "$result"
        elif $VERBOSE; then
            echo "Phase 0 detected (state.yaml): phases_completed includes [${found_phases}]"
        fi
        exit 0
    fi
fi

# ─── Option A: Fallback — check .spec-kit/ideation/ directory ────────────────

if [ -d "$IDEATION_DIR" ]; then
    # Count non-hidden files
    file_count=$(find "$IDEATION_DIR" -maxdepth 2 -type f ! -name ".*" 2>/dev/null | wc -l)
    if [ "$file_count" -gt 0 ]; then
        if $JSON; then
            echo "{\"phase0\":true,\"method\":\"directory\",\"phases\":[],\"files\":${file_count}}"
        elif $VERBOSE; then
            echo "Phase 0 detected (directory fallback): ${IDEATION_DIR} contains ${file_count} file(s)"
        fi
        exit 0
    fi
fi

# ─── Not detected ────────────────────────────────────────────────────────────

if $JSON; then
    echo '{"phase0":false,"method":"none","phases":[]}'
elif $VERBOSE; then
    echo "Phase 0 not detected"
fi
exit 1
