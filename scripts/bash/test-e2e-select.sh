#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(CDPATH="" cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(CDPATH="" cd "$SCRIPT_DIR/../.." && pwd)"
TMP_DIR="$(mktemp -d)"

cleanup() {
  rm -rf "$TMP_DIR"
}
trap cleanup EXIT

FILE_PATH="$TMP_DIR/idea_selection.md"

cat > "$FILE_PATH" <<'EOF'
# Idea Selection Report

## AI-RICE Scoring Table

| Idea ID | Reach | Impact | Confidence | Data_Readiness | Effort | Risk | AI-RICE Score |
|---------|-------|--------|------------|----------------|--------|------|---------------|
| S1      | 1000  | 2.0    | 70%        | 80%            | 4      | 3    | 93.3          |

## Selected Idea

**ID**: S1
**Text**: Selected idea text.
**Tag**: SEED
**AI-RICE Score**: 93.3

### Dimensional Breakdown

- **Reach**: 1000 - rationale
- **Impact**: 2.0 - rationale
- **Confidence**: 70% - rationale
- **Data_Readiness**: 80% - rationale
- **Effort**: 4 - rationale
- **Risk**: 3 - rationale
EOF

"$REPO_ROOT/scripts/bash/validate-airice.sh" "$FILE_PATH"
echo "SELECT E2E passed"
