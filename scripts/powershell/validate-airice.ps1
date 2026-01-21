param(
    [string]$FilePath = '.spec-kit/idea_selection.md'
)

$stateLog = 'scripts/powershell/state-log-violation.ps1'

if (-not (Test-Path $FilePath)) {
    Write-Error "idea_selection not found at $FilePath"
    if (Test-Path $stateLog) { & $stateLog 'select' 'Framework-Driven Development' 'idea_selection.md missing' 'critical' 'validate-airice' }
    exit 1
}

$header = (Select-String -Path $FilePath -Pattern '^\|' | Select-Object -First 1).Line
if (-not ($header -match 'Reach' -and $header -match 'Impact' -and $header -match 'Confidence' -and $header -match 'Data_Readiness' -and $header -match 'Effort' -and $header -match 'Risk')) {
    Write-Error 'AI-RICE scoring table header missing required columns'
    if (Test-Path $stateLog) { & $stateLog 'select' 'Framework-Driven Development' 'AI-RICE table missing required columns' 'high' 'validate-airice' }
    exit 1
}

$lines = (Select-String -Path $FilePath -Pattern '^\|' -AllMatches)
if ($lines.Count -lt 3) {
    Write-Error 'AI-RICE scoring table has no data rows'
    if (Test-Path $stateLog) { & $stateLog 'select' 'Framework-Driven Development' 'AI-RICE table has no data rows' 'high' 'validate-airice' }
    exit 1
}

$required = @('Reach','Impact','Confidence','Data_Readiness','Effort','Risk')
foreach ($item in $required) {
    if (-not (Select-String -Path $FilePath -Pattern "\*\*$item\*\*:" -SimpleMatch)) {
        Write-Error "Missing dimensional breakdown for $item"
        if (Test-Path $stateLog) { & $stateLog 'select' 'Traceability First' "Missing dimensional breakdown: $item" 'high' 'validate-airice' }
        exit 1
    }
}

Write-Output 'AI-RICE validation passed'
