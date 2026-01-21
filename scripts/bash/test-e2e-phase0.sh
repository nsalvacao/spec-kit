#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(CDPATH="" cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

"$SCRIPT_DIR/test-e2e-ideate.sh"
"$SCRIPT_DIR/test-e2e-select.sh"
"$SCRIPT_DIR/test-e2e-structure.sh"
"$SCRIPT_DIR/test-e2e-validate.sh"

echo "Phase 0 E2E passed"
