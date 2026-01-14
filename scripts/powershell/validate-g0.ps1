param(
    [string]$FilePath = '.spec-kit/vision_brief.md'
)

$stateLog = 'scripts/powershell/state-log-violation.ps1'

function Log-Violation {
    param(
        [string]$Message,
        [string]$Severity = 'high'
    )
    if (Test-Path $stateLog) { & $stateLog 'validate' 'Framework-Driven Development' $Message $Severity 'validate-g0' }
}

function Fail-Check {
    param(
        [string]$Message,
        [string]$Severity = 'high'
    )
    Write-Error $Message
    Log-Violation -Message $Message -Severity $Severity
    exit 1
}

if (-not (Test-Path $FilePath)) {
    Fail-Check "vision_brief.md not found at $FilePath" 'critical'
}

$requiredSections = @(
    'One-Liner',
    'Problem Statement',
    'Solution Approach',
    'Success Criteria',
    'Key Assumptions',
    'Data & Model Strategy',
    'Constraints & Risks'
)

foreach ($section in $requiredSections) {
    if (-not (Select-String -Path $FilePath -Pattern "^## $([regex]::Escape($section))" -CaseSensitive)) {
        Fail-Check "Missing section: $section"
    }
}

$content = Get-Content -Path $FilePath

$sectionRefs = @{}
foreach ($section in $requiredSections) { $sectionRefs[$section] = $false }
$currentSection = ''

foreach ($line in $content) {
    if ($line -match '^## ') {
        $currentSection = ($line -replace '^## ', '').Trim()
        continue
    }
    if ($currentSection -and $sectionRefs.ContainsKey($currentSection)) {
        if ($line -match 'Canvas References') {
            $sectionRefs[$currentSection] = $true
        }
    }
}

$missingRefs = @()
foreach ($section in $requiredSections) {
    if (-not $sectionRefs[$section]) { $missingRefs += $section }
}

if ($missingRefs.Count -gt 0) {
    Fail-Check ("Missing Canvas References in sections: {0}" -f ($missingRefs -join ', '))
}

if (Select-String -Path $FilePath -Pattern '\[PLACEHOLDER\]') {
    Fail-Check 'Found [PLACEHOLDER] tokens in vision_brief'
}

if (-not (Select-String -Path $FilePath -Pattern 'When .*I want .*so I can' -CaseSensitive:$false)) {
    Fail-Check 'Job statement missing When/I want/So I can format'
}

$section = ''
$subsection = ''
$assumptionCount = 0
$metricCount = 0
$dataSourceCount = 0
$modelWordCount = 0

foreach ($line in $content) {
    if ($line -match '^## ') {
        $section = ($line -replace '^## ', '').Trim()
        $subsection = ''
        continue
    }

    if ($section -eq 'Key Assumptions') {
        if ($line -match '^\|' -and $line -notmatch '^\|[ -]+\|' -and $line -notmatch '^\| *Assumption *\|') {
            $assumptionCount++
        }
        continue
    }

    if ($section -eq 'Success Criteria') {
        if ($line -match '^[0-9]+\.' -or $line -match '^- ') {
            $metricCount++
        }
        continue
    }

    if ($section -eq 'Data & Model Strategy') {
        if ($line -match '^\*\*Data Requirements\*\*') {
            $subsection = 'data'
            continue
        }
        if ($line -match '^\*\*Model Approach\*\*') {
            $subsection = 'model'
            $modelText = ($line -replace '^\*\*Model Approach\*\*:? ?', '')
            if ($modelText) {
                $modelWordCount += ($modelText -split '\s+' | Where-Object { $_ -ne '' }).Count
            }
            continue
        }
        if ($line -match '^\*\*') {
            $subsection = ''
            continue
        }

        if ($subsection -eq 'data' -and $line -match '^- ') {
            $dataSourceCount++
        }
        if ($subsection -eq 'model') {
            $modelWordCount += ($line -split '\s+' | Where-Object { $_ -ne '' }).Count
        }
    }
}

if ($assumptionCount -lt 3) {
    Fail-Check "Expected at least 3 assumptions, found $assumptionCount"
}

if ($metricCount -lt 3) {
    Fail-Check "Expected at least 3 success metrics, found $metricCount"
}

if ($dataSourceCount -lt 1) {
    Fail-Check "Expected at least 1 data source, found $dataSourceCount"
}

if ($modelWordCount -lt 50) {
    Fail-Check "Model approach must be at least 50 words, found $modelWordCount"
}

Write-Output 'Gate G0 automated checks passed'
