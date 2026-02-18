# validate-vision-brief.ps1 — Vision Brief validator with Waiver Mechanism
#
# Usage:
#   validate-vision-brief.ps1 [[-FilePath] <path>] [-Waive <hashtable>] [-ReportPath <path>]
#
# Examples:
#   .\validate-vision-brief.ps1
#   .\validate-vision-brief.ps1 .spec-kit/vision_brief.md
#   .\validate-vision-brief.ps1 -Waive @{ Q2 = "Metrics not finalised yet" }
#   .\validate-vision-brief.ps1 -Waive @{ Q2 = "justification"; AI4 = "budget TBD" } -ReportPath .spec-kit/g0_validation_report.md
#
# Automated checks (A1-A8) are non-waivable and always block on failure.
# Manual checks (Q1-Q5, AI1-AI4, C1-C3) may be waived with a justification.

param(
    [string]$FilePath = '.spec-kit/vision_brief.md',
    [hashtable]$Waive = @{},
    [string]$ReportPath = ''
)

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$stateLog = Join-Path $scriptDir 'state-log-violation.ps1'
$manualWarns = 0

function Write-LogViolation {
    param([string]$Message, [string]$Severity = 'high')
    if (Test-Path $stateLog -PathType Leaf) {
        & $stateLog 'validate' 'Framework-Driven Development' $Message $Severity 'validate-vision-brief'
    }
}

function Fail-Auto {
    param([string]$Criterion, [string]$Message)
    Write-Error "FAIL [$Criterion] $Message"
    Write-LogViolation $Message 'critical'
    exit 1
}

function Check-Manual {
    param([string]$Criterion, [string]$Label, [bool]$Passed, [string]$Detail)
    if ($Passed) {
        Write-Output "PASS [$Criterion] $Label"
        return
    }
    if ($Waive.ContainsKey($Criterion)) {
        Write-Output "WAIVED [$Criterion] $Label — $($Waive[$Criterion])"
        return
    }
    Write-Warning "WARN [$Criterion] ${Label}: $Detail"
    Write-Output "  -> To waive: -Waive @{ $Criterion = `"<justification>`" }"
    $script:manualWarns++
}

# ──────────────────────────────────────────────────────────────
# Automated Checks (non-waivable)
# ──────────────────────────────────────────────────────────────

Write-Output '=== Automated Checks (non-waivable) ==='

# A1: File exists
if (-not (Test-Path $FilePath -PathType Leaf)) { Fail-Auto 'A1' "vision_brief.md not found at $FilePath" }
Write-Output 'PASS [A1] vision_brief.md exists'

$content = Get-Content $FilePath -Raw
$lines = Get-Content $FilePath

# A2: All 7 required sections
$requiredSections = @('One-Liner','Problem Statement','Solution Approach','Success Criteria','Key Assumptions','Data & Model Strategy','Constraints & Risks')
$missingSections = @()
foreach ($section in $requiredSections) {
    if (-not ($lines | Select-String -Pattern "^## $([regex]::Escape($section))$")) {
        $missingSections += $section
    }
}
if ($missingSections.Count -gt 0) { Fail-Auto 'A2' "Missing sections: $($missingSections -join ', ')" }
Write-Output 'PASS [A2] All 7 sections present'

# A3: No [PLACEHOLDER] tokens
if ($content -match '\[PLACEHOLDER\]') { Fail-Auto 'A3' 'Found [PLACEHOLDER] tokens in vision_brief' }
Write-Output 'PASS [A3] No placeholder tokens'

# A4: Job statement format
if (-not ($content -imatch 'When .*I want .*so I can')) { Fail-Auto 'A4' "Job statement missing 'When/I want/So I can' format" }
Write-Output 'PASS [A4] Job statement format valid'

# A5: ≥3 assumptions
$inKeyAssumptions = $false
$assumptionCount = 0
foreach ($line in $lines) {
    if ($line -match '^## Key Assumptions') { $inKeyAssumptions = $true; continue }
    if ($line -match '^## ' -and $inKeyAssumptions) { break }
    if ($inKeyAssumptions -and $line -match '^\|' -and $line -notmatch '^\|[ -]+\|' -and $line -notmatch '^\| *Assumption *\|') {
        $assumptionCount++
    }
}
if ($assumptionCount -lt 3) { Fail-Auto 'A5' "Expected >=3 assumptions, found $assumptionCount" }
Write-Output "PASS [A5] >=3 assumptions (found $assumptionCount)"

# A6: ≥3 metrics
$inSuccessCriteria = $false
$metricCount = 0
foreach ($line in $lines) {
    if ($line -match '^## Success Criteria') { $inSuccessCriteria = $true; continue }
    if ($line -match '^## ' -and $inSuccessCriteria) { break }
    if ($inSuccessCriteria -and ($line -match '^\d+\.' -or $line -match '^- ')) { $metricCount++ }
}
if ($metricCount -lt 3) { Fail-Auto 'A6' "Expected >=3 metrics, found $metricCount" }
Write-Output "PASS [A6] >=3 metrics (found $metricCount)"

# A7: ≥1 data source
$inDataModel = $false
$inDataReq = $false
$dataSourceCount = 0
foreach ($line in $lines) {
    if ($line -match '^## Data & Model Strategy') { $inDataModel = $true; $inDataReq = $false; continue }
    if ($line -match '^## ' -and $inDataModel) { break }
    if ($inDataModel -and $line -match '^\*\*Data Requirements\*\*') { $inDataReq = $true; continue }
    if ($inDataModel -and $inDataReq -and $line -match '^\*\*') { $inDataReq = $false }
    if ($inDataModel -and $inDataReq -and $line -match '^- ') { $dataSourceCount++ }
}
if ($dataSourceCount -lt 1) { Fail-Auto 'A7' "Expected >=1 data source, found $dataSourceCount" }
Write-Output "PASS [A7] >=1 data source (found $dataSourceCount)"

# A8: Model approach ≥50 words
$inDataModel = $false
$inModelApproach = $false
$modelWords = 0
foreach ($line in $lines) {
    if ($line -match '^## Data & Model Strategy') { $inDataModel = $true; $inModelApproach = $false; continue }
    if ($line -match '^## ' -and $inDataModel) { break }
    if ($inDataModel -and $line -match '^\*\*Model Approach\*\*') {
        $inModelApproach = $true
        $stripped = $line -replace '^\*\*Model Approach\*\*:? ?', ''
        if ($stripped.Trim()) { $modelWords += ($stripped -split '\s+').Count }
        continue
    }
    if ($inDataModel -and $inModelApproach -and $line -match '^\*\*') { $inModelApproach = $false }
    if ($inDataModel -and $inModelApproach -and $line.Trim()) {
        $modelWords += ($line -split '\s+').Count
    }
}
if ($modelWords -lt 50) { Fail-Auto 'A8' "Model approach must be >=50 words, found $modelWords" }
Write-Output "PASS [A8] Model approach >=50 words (found $modelWords)"

# ──────────────────────────────────────────────────────────────
# Manual Checks — Quality (waivable)
# ──────────────────────────────────────────────────────────────

Write-Output ''
Write-Output '=== Manual Checks — Quality (waivable) ==='

# Q1: Assumptions have validation methods
$hasValidationMethods = [bool]($content -match 'Validation Method')
Check-Manual 'Q1' 'Assumptions have validation methods' $hasValidationMethods 'Assumption table missing Validation Method column'

# Q2: Metrics are SMART
$hasSmartMetrics = [bool]($content -imatch '(by |within |Q\d|month|week|year|target:|%|>=|<=)')
Check-Manual 'Q2' 'Metrics are SMART' $hasSmartMetrics "No measurable/time-bound metric indicators found"

# Q3: Data sources with availability %
$hasConcreteSources = [bool]($content -match '\d+\s*%')
Check-Manual 'Q3' 'Data sources concrete with availability %' $hasConcreteSources 'No availability % found in data sources'

# Q4: Model rationale present
$hasModelRationale = $modelWords -ge 20
Check-Manual 'Q4' 'Model rationale present' $hasModelRationale 'Model Approach section appears too brief'

# Q5: Risk mitigations defined
$hasMitigations = [bool]($content -imatch '(mitigation|mitigate|controls?)')
Check-Manual 'Q5' 'Risk mitigations defined' $hasMitigations 'No mitigation language found'

# ──────────────────────────────────────────────────────────────
# Manual Checks — AI-Specific (waivable)
# ──────────────────────────────────────────────────────────────

Write-Output ''
Write-Output '=== Manual Checks — AI-Specific (waivable) ==='

# AI1: Data readiness ≥60%
$hasReadiness = [bool]($content -match '[6-9]\d%|100%')
Check-Manual 'AI1' 'Data readiness >=60%' $hasReadiness 'No data readiness >=60% found'

# AI2: Evaluation strategy defined
$hasEval = [bool]($content -imatch '(evaluation|benchmark|accuracy|precision|recall|F1|BLEU|rouge)')
Check-Manual 'AI2' 'Evaluation strategy defined' $hasEval 'No evaluation metrics/benchmarks found'

# AI3: Safety assessment complete
$hasSafety = [bool]($content -imatch '(safety|risk|bias|hallucination|compliance|regulatory)')
Check-Manual 'AI3' 'Safety assessment complete' $hasSafety 'No safety/risk language found'

# AI4: Cost viability aligned
$hasCost = [bool]($content -imatch '(budget|cost|viabilit|pricing|inference)')
Check-Manual 'AI4' 'Cost viability aligned' $hasCost 'No cost/budget reference found'

# ──────────────────────────────────────────────────────────────
# Manual Checks — Consistency (waivable)
# ──────────────────────────────────────────────────────────────

Write-Output ''
Write-Output '=== Manual Checks — Consistency (waivable) ==='

# C1: Canvas References in all sections
$allHaveRefs = $true
foreach ($section in $requiredSections) {
    $inSection = $false
    $hasRef = $false
    foreach ($line in $lines) {
        if ($line -match "^## $([regex]::Escape($section))") { $inSection = $true; continue }
        if ($line -match '^## ' -and $inSection) { break }
        if ($inSection -and $line -match 'Canvas References') { $hasRef = $true }
    }
    if (-not $hasRef) { $allHaveRefs = $false; break }
}
Check-Manual 'C1' 'Canvas References present in all sections' $allHaveRefs "One or more sections missing 'Canvas References'"

# C2: Solution aligned with AI task
$hasAlignment = [bool]($content -imatch '(AI Task|canvas.*C12|C12.*canvas)')
Check-Manual 'C2' 'Solution aligned with AI task (C12 reference)' $hasAlignment 'No explicit C12 (AI Task) reference found'

# C3: Constraints aligned with model choice
$hasConstraintsModel = [bool]($content -imatch '(latency|constraint.*model|model.*constraint|C17|C14)')
Check-Manual 'C3' 'Constraints aligned with model choice' $hasConstraintsModel 'No explicit constraint-model alignment found'

# ──────────────────────────────────────────────────────────────
# Waiver registration in report
# ──────────────────────────────────────────────────────────────

if ($Waive.Count -gt 0 -and $ReportPath -and (Test-Path $ReportPath -PathType Leaf)) {
    Write-Output ''
    Write-Output '=== Registering Waivers in Report ==='
    $timestamp = (Get-Date -Format 'yyyy-MM-ddTHH:mm:ssZ')
    $reportContent = Get-Content $ReportPath -Raw
    $waiversSection = "## Waivers"
    if ($reportContent -match [regex]::Escape($waiversSection)) {
        $waiversBlock = "`n"
        $waiverNum = 1
        foreach ($criterion in $Waive.Keys) {
            $justification = $Waive[$criterion]
            $waiversBlock += "### Waiver W${waiverNum}: ${criterion}`n"
            $waiversBlock += "**Justification**: ${justification}`n"
            $waiversBlock += "**Approved By**: validate-vision-brief.ps1 (automated waiver registration)`n"
            $waiversBlock += "**Timestamp**: ${timestamp}`n`n"
            $waiverNum++
        }
        $reportContent = $reportContent.Replace($waiversSection, "$waiversSection$waiversBlock")
        Set-Content $ReportPath $reportContent -NoNewline
        Write-Output "Waivers registered in $ReportPath"
    } else {
        Write-Warning "No '## Waivers' section found in $ReportPath — waivers not registered"
    }
}

# ──────────────────────────────────────────────────────────────
# Final result
# ──────────────────────────────────────────────────────────────

Write-Output ''

if ($manualWarns -gt 0) {
    $msg = "$manualWarns manual check(s) unresolved"
    Write-Error "RESULT: FAIL — $msg"
    Write-LogViolation $msg 'high'
    exit 1
} elseif ($Waive.Count -gt 0) {
    Write-Output "RESULT: PASS WITH WAIVER — all automated checks passed; $($Waive.Count) waiver(s) applied"
} else {
    Write-Output 'RESULT: PASS — all checks passed'
}
