param(
    [Parameter(ValueFromRemainingArguments=$true)]
    [string[]]$ArgsList
)

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$pythonScript = Join-Path (Split-Path -Parent $scriptDir) 'python/handoff-metadata-lint.py'

if (Get-Command uv -ErrorAction SilentlyContinue) {
    & uv run python $pythonScript @ArgsList
    exit $LASTEXITCODE
}

if (Get-Command python3 -ErrorAction SilentlyContinue) {
    & python3 $pythonScript @ArgsList
    exit $LASTEXITCODE
}

Write-Error 'Neither uv nor python3 is available. Please install Python 3 (or uv).'
exit 1
