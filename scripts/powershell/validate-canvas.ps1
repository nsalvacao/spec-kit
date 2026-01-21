param(
    [string]$FilePath = '.spec-kit/ai_vision_canvas.md'
)

$stateLog = 'scripts/powershell/state-log-violation.ps1'

if (-not (Test-Path $FilePath)) {
    Write-Error "ai_vision_canvas not found at $FilePath"
    if (Test-Path $stateLog) { & $stateLog 'structure' 'Framework-Driven Development' 'ai_vision_canvas.md missing' 'critical' 'validate-canvas' }
    exit 1
}

$requiredSections = @(
    '### 1. Job Statement (When/Want/So)',
    '### 2. Job Executor',
    '### 3. Job Context',
    '### 4. Desired Outcomes',
    '### 5. Current Solution Pains',
    '### 6. Top 3 Problems',
    '### 7. Solution (High-Level)',
    '### 8. Key Assumptions (Critical, Unvalidated)',
    '### 9. Validation Methods (Build-Measure-Learn)',
    '### 10. Key Metrics (Success Criteria)',
    '### 11. Cost Structure (Budget Constraints)',
    '### 12. AI Task',
    '### 13. Data Requirements',
    '### 14. Model Approach',
    '### 15. Evaluation Strategy',
    '### 16. Safety & Risk',
    '### 17. Constraints',
    '### 18. Infrastructure (High-Level)'
)

$missing = @()
foreach ($section in $requiredSections) {
    if (-not (Select-String -Path $FilePath -Pattern [regex]::Escape($section))) {
        $missing += $section
    }
}

if ($missing.Count -gt 0) {
    Write-Error ("Missing canvas sections: {0}" -f ($missing -join '; '))
    if (Test-Path $stateLog) { & $stateLog 'structure' 'Framework-Driven Development' ("Missing canvas sections: {0}" -f ($missing -join '; ')) 'high' 'validate-canvas' }
    exit 1
}

$sectionCount = (Select-String -Path $FilePath -Pattern '^### [0-9]+\.' -AllMatches).Count
if ($sectionCount -lt 18) {
    Write-Error "Expected 18 canvas components, found $sectionCount"
    if (Test-Path $stateLog) { & $stateLog 'structure' 'Framework-Driven Development' "Canvas components missing: $sectionCount/18" 'high' 'validate-canvas' }
    exit 1
}

if (-not (Select-String -Path $FilePath -Pattern 'When .*I want .*so I can' -CaseSensitive:$false)) {
    Write-Error 'Job statement missing When/I want/So I can format'
    if (Test-Path $stateLog) { & $stateLog 'structure' 'Framework-Driven Development' 'Job statement missing When/I want/So I can format' 'high' 'validate-canvas' }
    exit 1
}

if (Select-String -Path $FilePath -Pattern '\[PLACEHOLDER\]') {
    Write-Error 'Found [PLACEHOLDER] tokens in canvas'
    if (Test-Path $stateLog) { & $stateLog 'structure' 'Framework-Driven Development' 'Found [PLACEHOLDER] tokens in canvas' 'high' 'validate-canvas' }
    exit 1
}

Write-Output 'Vision canvas validation passed'
