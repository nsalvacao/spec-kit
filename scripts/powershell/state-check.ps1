param(
    [Parameter(Mandatory=$true)][string]$RequiredPhase
)

$stateFile = '.spec-kit/state.yaml'

if (-not (Get-Command python3 -ErrorAction SilentlyContinue)) {
    Write-Error 'python3 not found. Please install Python 3'
    exit 1
}

if (-not (Test-Path $stateFile)) {
    Write-Error 'state.yaml not found. Run state-init.ps1 first.'
    exit 1
}

# Use Python to check if the phase is in phases_completed array
$pythonCode = @"
import yaml
import sys
with open('$stateFile', 'r') as f:
    data = yaml.safe_load(f)
phases = data.get('phases_completed', [])
if '$RequiredPhase' in phases:
    sys.exit(0)
else:
    sys.exit(1)
"@

$result = python3 -c $pythonCode
if ($LASTEXITCODE -ne 0) {
    Write-Error "Phase '$RequiredPhase' must be completed first."
    exit 1
}
