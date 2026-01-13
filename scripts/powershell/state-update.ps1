param(
    [Parameter(Mandatory=$true)][string]$Expression
)

$stateFile = '.spec-kit/state.yaml'
$tempFile = '.spec-kit/.state.yaml.tmp'

if (-not (Get-Command yq -ErrorAction SilentlyContinue)) {
    Write-Error 'yq not found. Install: https://github.com/mikefarah/yq'
    exit 1
}

if (-not (Test-Path $stateFile)) {
    Write-Error 'state.yaml not found. Run state-init.ps1 first.'
    exit 1
}

# Ensure violations array exists
$expr = ".violations //= [] | $Expression"

$null = yq e $expr $stateFile | Set-Content -Path $tempFile -NoNewline
Move-Item -Force $tempFile $stateFile
