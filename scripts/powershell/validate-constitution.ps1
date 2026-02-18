# validate-constitution.ps1 — Constitution validator with Waiver Mechanism
#
# Usage:
#   validate-constitution.ps1 [[-FilePath] <path>] [-Waive <hashtable>] [-ReportPath <path>]
#
# Examples:
#   .\validate-constitution.ps1
#   .\validate-constitution.ps1 .specify/constitution.md
#   .\validate-constitution.ps1 -Waive @{ Q1 = "Phase 0 not used; principles from README" }
#   .\validate-constitution.ps1 -Waive @{ P1 = "justification" } -ReportPath .specify/constitution-validation.md
#
# Automated checks (A1-A8) are non-waivable and always block on failure.
# Manual checks (Q1-Q4, P1-P2) may be waived with a justification.

param(
    [string]$FilePath   = '.specify/constitution.md',
    [hashtable]$Waive   = @{},
    [string]$ReportPath = ''
)

$scriptDir  = Split-Path -Parent $MyInvocation.MyCommand.Path
$stateLog   = Join-Path $scriptDir 'state-log-violation.ps1'
$manualWarns = 0

function Write-LogViolation {
    param([string]$Message, [string]$Severity = 'high')
    if (Test-Path $stateLog -PathType Leaf) {
        & $stateLog 'validate' 'Framework-Driven Development' $Message $Severity 'validate-constitution'
    }
}

# Validate file paths stay within project directory
$projectDir = (Resolve-Path .).Path
if ((Test-Path $FilePath) -and -not (Resolve-Path $FilePath).Path.StartsWith($projectDir)) {
    Write-Error "Error: FilePath '$FilePath' is outside the project directory."
    exit 1
}
if ($ReportPath -and (Test-Path $ReportPath) -and -not (Resolve-Path $ReportPath).Path.StartsWith($projectDir)) {
    Write-Error "Error: ReportPath '$ReportPath' is outside the project directory."
    exit 1
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
if (-not (Test-Path $FilePath -PathType Leaf)) {
    Fail-Auto 'A1' "Constitution file not found at '$FilePath'"
}
Write-Output 'PASS [A1] Constitution file exists'

$content = Get-Content $FilePath -Raw
$lines   = Get-Content $FilePath

# A2: File not empty (>= 20 lines)
if ($lines.Count -lt 20) {
    Fail-Auto 'A2' "Constitution file too short ($($lines.Count) lines); expected >= 20"
}
Write-Output "PASS [A2] File has $($lines.Count) lines (>= 20)"

# A3: Section '## Core Principles' present
if (-not ($lines | Select-String -Pattern '^## Core Principles$')) {
    Fail-Auto 'A3' "Missing required section: '## Core Principles'"
}
Write-Output 'PASS [A3] Section ## Core Principles present'

# A4: Section '## Governance' present
if (-not ($lines | Select-String -Pattern '^## Governance$')) {
    Fail-Auto 'A4' "Missing required section: '## Governance'"
}
Write-Output 'PASS [A4] Section ## Governance present'

# A5: Metadata present (**Version**: and **Ratified**:)
if (-not ($content -match 'Version\*\*:')) {
    Fail-Auto 'A5' "Missing metadata '**Version**:' line in constitution"
}
if (-not ($content -match 'Ratified\*\*:')) {
    Fail-Auto 'A5' "Missing metadata '**Ratified**:' date in constitution"
}
Write-Output 'PASS [A5] Metadata (Version/Ratified) present'

# A6: Unfilled template placeholders
$unfilled = @(
    '\[PROJECT_NAME\]',
    '\[PRINCIPLE_\d+_NAME\]',
    '\[PRINCIPLE_\d+_DESCRIPTION\]',
    '\[SECTION_\d+_NAME\]',
    '\[SECTION_\d+_CONTENT\]',
    '\[GOVERNANCE_RULES\]',
    '\[CONSTITUTION_VERSION\]',
    '\[RATIFICATION_DATE\]',
    '\[LAST_AMENDED_DATE\]'
)
foreach ($token in $unfilled) {
    if ($content -match $token) {
        Fail-Auto 'A6' "Unfilled template placeholder found: $token"
    }
}
Write-Output 'PASS [A6] No unfilled template placeholders'

# A7: At least 3 principles (### headers inside Core Principles section)
$inPrinciples   = $false
$principleCount = 0
foreach ($line in $lines) {
    if ($line -match '^## Core Principles') { $inPrinciples = $true; continue }
    if ($line -match '^## ' -and $inPrinciples) { $inPrinciples = $false }
    if ($inPrinciples -and $line -match '^### ') { $principleCount++ }
}
if ($principleCount -lt 3) {
    Fail-Auto 'A7' "Too few principles defined ($principleCount); expected >= 3 (### sub-headers in Core Principles)"
}
Write-Output "PASS [A7] $principleCount principles defined (>= 3)"

# A8: Governance section has substantive content
$inGovernance    = $false
$governanceLines = 0
foreach ($line in $lines) {
    if ($line -match '^## Governance') { $inGovernance = $true; continue }
    if ($line -match '^## ' -and $inGovernance) { $inGovernance = $false }
    if ($inGovernance -and $line -notmatch '^[#<]' -and $line.Length -gt 5) { $governanceLines++ }
}
if ($governanceLines -lt 1) {
    Fail-Auto 'A8' 'Governance section has no substantive content (only comments/headers)'
}
Write-Output "PASS [A8] Governance has $governanceLines substantive line(s)"

# ──────────────────────────────────────────────────────────────
# Manual Checks (waivable)
# ──────────────────────────────────────────────────────────────

Write-Output ''
Write-Output '=== Manual Checks ==='

# Q1: Phase 0 integration comment block removed
$hasPhase0Block = $content -match 'PHASE 0 INTEGRATION CHECK'
Check-Manual 'Q1' 'Phase 0 integration comment block removed' (-not $hasPhase0Block) `
    "Template comment block 'PHASE 0 INTEGRATION CHECK' still present; derive principles from Phase 0 artifacts and remove the comment"

# Q2: Each principle has substantive description (> 20 chars total description content)
$inPrinciplesQ2 = $false
$currentDesc    = 0
$shortCount     = 0
foreach ($line in $lines) {
    if ($line -match '^## Core Principles') { $inPrinciplesQ2 = $true; continue }
    if ($line -match '^## ' -and $inPrinciplesQ2) { $inPrinciplesQ2 = $false }
    if ($inPrinciplesQ2 -and $line -match '^### ') {
        if ($currentDesc -gt 0 -and $currentDesc -le 20) { $shortCount++ }
        $currentDesc = 0; continue
    }
    if ($inPrinciplesQ2 -and $line -notmatch '^[#<]' -and $line.Length -gt 3) {
        $currentDesc += $line.Length
    }
}
if ($currentDesc -gt 0 -and $currentDesc -le 20) { $shortCount++ }

Check-Manual 'Q2' 'All principles have substantive descriptions (> 20 chars)' ($shortCount -eq 0) `
    "$shortCount principle(s) have very short or missing descriptions"

# Q3: Governance section references amendment or compliance process
$hasGovernanceProcess = $content -match '(?i)(amendment|amend|compliance|supersede|ratif|review process|update process)'
Check-Manual 'Q3' 'Governance includes amendment/compliance process' $hasGovernanceProcess `
    'No amendment or compliance process found in Governance section'

# Q4: At least one additional section beyond Core Principles and Governance
$extraSections  = 0
$skipSection    = $false
foreach ($line in $lines) {
    if ($line -match '^## (Core Principles|Governance)') { $skipSection = $true; continue }
    if ($skipSection -and $line -match '^## ') { $skipSection = $false }
    if (-not $skipSection -and $line -match '^## ') { $extraSections++ }
}
Check-Manual 'Q4' 'At least one additional section (e.g. Constraints, Workflow, Quality Gates)' ($extraSections -ge 1) `
    'Only Core Principles and Governance found; add at least one domain-specific section'

# P1: Phase 0 artifacts referenced
$hasPhase0Ref = $content -match '(?i)(\.spec-kit/|ai_vision_canvas|ideas_backlog|idea_selection|g0_validation|vision_brief)'
Check-Manual 'P1' 'Phase 0 artifacts referenced in constitution' $hasPhase0Ref `
    'No references to .spec-kit/ Phase 0 artifacts found; if Phase 0 was not used, waive with justification'

# P2: AI/ML principles present if canvas declares AI Task (conditional)
$canvasFile = '.spec-kit/ai_vision_canvas.md'
if ((Test-Path $canvasFile -PathType Leaf) -and (Get-Content $canvasFile -Raw) -match '(?i)(C12|AI Task|machine learning|model)') {
    $hasAiPrinciples = $content -match '(?i)(model|inference|ai|ml|data|accuracy|safety|fairness|bias)'
    Check-Manual 'P2' 'AI/ML principles present (canvas declares AI Task C12)' $hasAiPrinciples `
        'Canvas declares AI task but constitution has no AI/ML principles'
} else {
    Write-Output 'SKIP [P2] AI/ML principles check (no AI canvas or C12 reference found)'
}

# ──────────────────────────────────────────────────────────────
# Waiver registration in report
# ──────────────────────────────────────────────────────────────

if ($Waive.Count -gt 0 -and $ReportPath -ne '' -and (Test-Path $ReportPath -PathType Leaf)) {
    Write-Output ''
    Write-Output '=== Registering Waivers in Report ==='
    $waiversBlock = ''
    foreach ($key in $Waive.Keys) {
        $waiversBlock += "| $key | $($Waive[$key]) |`n"
    }
    $reportContent  = Get-Content $ReportPath -Raw
    $waiversSection = '## Waivers'
    if ($reportContent -match [regex]::Escape($waiversSection)) {
        # Idempotent: remove previously inserted table rows, then insert fresh ones
        $lines = $reportContent -split "`n"
        $newLines = [System.Collections.Generic.List[string]]::new()
        $inWaivers = $false
        foreach ($line in $lines) {
            if ($line -match '^## Waivers') {
                $newLines.Add($line)
                $newLines.Add('')
                $newLines.Add($waiversBlock.TrimEnd())
                $inWaivers = $true
                continue
            }
            if ($inWaivers -and $line -match '^\| ') { continue }
            $inWaivers = $false
            $newLines.Add($line)
        }
        Set-Content -Path $ReportPath -Value ($newLines -join "`n") -NoNewline
        Write-Output "Waivers registered in $ReportPath"
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
