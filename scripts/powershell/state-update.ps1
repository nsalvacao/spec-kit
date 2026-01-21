# This script is deprecated and only shows usage information.
# Direct usage of the Python implementation is required.

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$pythonScript = Join-Path (Split-Path -Parent $scriptDir) 'python/state-update.py'

Write-Error @"
Error: state-update.ps1 is deprecated. Use the Python implementation directly:
  python3 $pythonScript --file .spec-kit/state.yaml --operation <operation> [options]

Available operations:
  - set-value: Set a key to a value
  - append-item: Append to an array
  - ensure-array: Ensure key is an array
  - log-violation: Log a violation
  - set-multiple: Set multiple keys (JSON)

Run 'python3 $pythonScript --help' for detailed usage.
"@
exit 1
