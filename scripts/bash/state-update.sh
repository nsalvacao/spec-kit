#!/usr/bin/env bash
set -euo pipefail

# This script is deprecated. Use the Python implementation directly.
# This wrapper is kept for backwards compatibility but now calls Python.

SCRIPT_DIR="$(CDPATH="" cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_SCRIPT="$SCRIPT_DIR/../python/state-update.py"

echo "Error: state-update.sh is deprecated. Use the Python implementation directly:" >&2
echo "  python3 $PYTHON_SCRIPT --file .spec-kit/state.yaml --operation <operation> [options]" >&2
echo "" >&2
echo "Available operations:" >&2
echo "  - set-value: Set a key to a value" >&2
echo "  - append-item: Append to an array" >&2
echo "  - ensure-array: Ensure key is an array" >&2
echo "  - log-violation: Log a violation" >&2
echo "  - set-multiple: Set multiple keys (JSON)" >&2
echo "" >&2
echo "Run 'python3 $PYTHON_SCRIPT --help' for detailed usage." >&2
exit 1
