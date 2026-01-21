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
# Pass values as command-line arguments to avoid code injection
$pythonCode = @'
import yaml
import sys

state_file = sys.argv[1]
required_phase = sys.argv[2]

with open(state_file, 'r') as f:
    data = yaml.safe_load(f)
phases = data.get('phases_completed', [])
if required_phase in phases:
    sys.exit(0)
else:
    sys.exit(1)
'@

$result = python3 -c $pythonCode $stateFile $RequiredPhase
if ($LASTEXITCODE -ne 0) {
    Write-Error "Phase '$RequiredPhase' must be completed first."
    exit 1
}
