param(
    [string]$FilePath = '.ideas/evaluation-results.md',
    [string]$ProjectDir = '.'
)

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$runtimeScript = Join-Path (Split-Path -Parent $scriptDir) 'strategic-review-runtime.py'

if (-not (Test-Path -LiteralPath $runtimeScript -PathType Leaf)) {
    Write-Error "strategic-review runtime helper not found at $runtimeScript"
    exit 1
}

$python = Get-Command python -ErrorAction SilentlyContinue
if (-not $python) {
    $python = Get-Command python3 -ErrorAction SilentlyContinue
}
if (-not $python) {
    Write-Error 'python/python3 not found in PATH.'
    exit 1
}

& $python.Source $runtimeScript --mode validate --file $FilePath --project-root $ProjectDir
if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}
