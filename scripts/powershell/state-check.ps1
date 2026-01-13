param(
    [Parameter(Mandatory=$true)][string]$RequiredPhase
)

$stateFile = '.spec-kit/state.yaml'

if (-not (Get-Command yq -ErrorAction SilentlyContinue)) {
    Write-Error 'yq not found. Install: https://github.com/mikefarah/yq'
    exit 1
}

if (-not (Test-Path $stateFile)) {
    Write-Error 'state.yaml not found. Run state-init.ps1 first.'
    exit 1
}

$contains = yq e ".phases_completed | contains([\"$RequiredPhase\"])" $stateFile
if ($contains -notmatch 'true') {
    Write-Error "Phase '$RequiredPhase' must be completed first."
    exit 1
}
