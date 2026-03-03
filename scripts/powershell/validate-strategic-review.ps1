param(
    [string]$FilePath = '.ideas/evaluation-results.md',
    [string]$ProjectDir = '.'
)

$ErrorActionPreference = 'Stop'

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$runtimeScript = Join-Path (Split-Path -Parent $scriptDir) 'strategic-review-runtime.py'

if (-not (Test-Path -LiteralPath $runtimeScript -PathType Leaf)) {
    Write-Error "strategic-review runtime helper not found at $runtimeScript"
    exit 1
}

function Resolve-CommandPath {
    param(
        [Parameter(Mandatory = $true)]
        [System.Management.Automation.CommandInfo]$CommandInfo
    )

    if ($CommandInfo.PSObject.Properties.Name -contains 'Path' -and $CommandInfo.Path) {
        return $CommandInfo.Path
    }
    return $CommandInfo.Source
}

function Test-PythonCompatible {
    param(
        [Parameter(Mandatory = $true)]
        [string]$ExecutablePath
    )

    $versionTuple = & $ExecutablePath -c "import sys; print(f'{sys.version_info[0]}.{sys.version_info[1]}')" 2>$null
    if ($LASTEXITCODE -ne 0) {
        return $false
    }

    $version = $null
    if (-not [Version]::TryParse("$versionTuple".Trim(), [ref]$version)) {
        return $false
    }
    return $version -ge [Version]'3.9'
}

$uv = Get-Command uv -ErrorAction SilentlyContinue
if ($uv) {
    $uvPath = Resolve-CommandPath -CommandInfo $uv
    & $uvPath run python $runtimeScript --mode validate --file $FilePath --project-root $ProjectDir
    exit $LASTEXITCODE
}

$python = Get-Command python3 -ErrorAction SilentlyContinue
if (-not $python) {
    $python = Get-Command python -ErrorAction SilentlyContinue
}
if (-not $python) {
    Write-Error 'Neither uv nor python3/python was found in PATH.'
    exit 1
}

$pythonPath = Resolve-CommandPath -CommandInfo $python
if (-not (Test-PythonCompatible -ExecutablePath $pythonPath)) {
    Write-Error "Python >= 3.9 is required to run strategic-review runtime (found: $pythonPath)."
    exit 1
}

& $pythonPath $runtimeScript --mode validate --file $FilePath --project-root $ProjectDir
exit $LASTEXITCODE
