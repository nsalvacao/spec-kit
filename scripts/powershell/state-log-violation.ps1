param(
    [Parameter(Mandatory=$true)][string]$Phase,
    [Parameter(Mandatory=$true)][string]$Principle,
    [Parameter(Mandatory=$true)][string]$Message,
    [string]$Severity = 'high',
    [string]$Source = 'validator'
)

$stateFile = '.spec-kit/state.yaml'
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$pythonScript = Join-Path (Split-Path -Parent $scriptDir) 'python/state-update.py'

if (-not (Get-Command python3 -ErrorAction SilentlyContinue)) {
    Write-Error 'python3 not found. Please install Python 3'
    exit 1
}

if (-not (Test-Path $stateFile)) {
    Write-Error 'state.yaml not found. Run state-init.ps1 first.'
    exit 1
}

& python3 $pythonScript `
  --file $stateFile `
  --operation log-violation `
  --violation-phase $Phase `
  --violation-principle $Principle `
  --violation-message $Message `
  --violation-severity $Severity `
  --violation-source $Source
