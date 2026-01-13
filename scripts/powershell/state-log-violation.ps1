param(
    [Parameter(Mandatory=$true)][string]$Phase,
    [Parameter(Mandatory=$true)][string]$Principle,
    [Parameter(Mandatory=$true)][string]$Message,
    [string]$Severity = 'high',
    [string]$Source = 'validator'
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

$timestamp = (Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ')

$expr = ".violations += [{\"timestamp\":\"$timestamp\",\"phase\":\"$Phase\",\"principle\":\"$Principle\",\"message\":\"$Message\",\"severity\":\"$Severity\",\"source\":\"$Source\"}]"

yq e $expr $stateFile | Set-Content -Path $tempFile -NoNewline
Move-Item -Force $tempFile $stateFile
