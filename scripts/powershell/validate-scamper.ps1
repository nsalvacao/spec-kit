param(
    [string]$FilePath = '.spec-kit/ideas_backlog.md'
)

$stateLog = 'scripts/powershell/state-log-violation.ps1'

if (-not (Test-Path $FilePath)) {
    Write-Error "ideas_backlog not found at $FilePath"
    if (Test-Path $stateLog) { & $stateLog 'ideate' 'Framework-Driven Development' 'ideas_backlog.md missing' 'critical' 'validate-scamper' }
    exit 1
}

$required = @(
    'SCAMPER-Substitute',
    'SCAMPER-Combine',
    'SCAMPER-Adapt',
    'SCAMPER-Modify',
    'SCAMPER-Put-to-another-use',
    'SCAMPER-Eliminate',
    'SCAMPER-Reverse'
)

$missing = @()
foreach ($lens in $required) {
    if (-not (Select-String -Path $FilePath -Pattern "(\*\*Tag\*\*|Tag): $lens")) {
        $missing += $lens
    }
}

if ($missing.Count -gt 0) {
    Write-Error "Missing SCAMPER lenses: $($missing -join ', ')"
    if (Test-Path $stateLog) { & $stateLog 'ideate' 'Framework-Driven Development' "Missing SCAMPER lenses: $($missing -join ', ')" 'high' 'validate-scamper' }
    exit 1
}

$hmwCount = (Select-String -Path $FilePath -Pattern '(\*\*Tag\*\*|Tag): HMW-' -AllMatches).Count
if ($hmwCount -lt 5) {
    Write-Error "Expected at least 5 HMW ideas, found $hmwCount"
    if (Test-Path $stateLog) { & $stateLog 'ideate' 'Framework-Driven Development' "Insufficient HMW ideas: $hmwCount" 'high' 'validate-scamper' }
    exit 1
}

$ideaCount = (Select-String -Path $FilePath -Pattern '\*\*Tag\*\*: ' -AllMatches).Count
if ($ideaCount -lt 8) {
    Write-Error "Expected at least 8 total ideas, found $ideaCount"
    if (Test-Path $stateLog) { & $stateLog 'ideate' 'Framework-Driven Development' "Insufficient total ideas: $ideaCount" 'high' 'validate-scamper' }
    exit 1
}

$nonSeedCount = (Select-String -Path $FilePath -Pattern '(\*\*Tag\*\*|Tag): (SCAMPER|HMW)-' -AllMatches).Count
$provCount = (Select-String -Path $FilePath -Pattern '^\*\*Provenance\*\*: ' -AllMatches).Count
if ($provCount -lt $nonSeedCount) {
    Write-Error 'Missing Provenance fields for non-seed ideas'
    if (Test-Path $stateLog) { & $stateLog 'ideate' 'Traceability First' 'Missing provenance on non-seed ideas' 'high' 'validate-scamper' }
    exit 1
}

Write-Output 'SCAMPER/HMW validation passed'
