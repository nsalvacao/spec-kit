param(
    [string]$FilePath = '.ideas/brainstorm-expansion.md'
)

if (-not (Test-Path $FilePath)) {
    Write-Error "brainstorm document not found at $FilePath"
    exit 1
}

$content = Get-Content -Path $FilePath -Raw -Encoding UTF8
$lines = Get-Content -Path $FilePath -Encoding UTF8

$requiredSections = @(
    '^## 1\. What Is the REAL Asset\?$',
    '^## 2\. SCAMPER Analysis$',
    '^## 3\. Divergent Ideation',
    '^## 4\. Convergent Analysis',
    '^## 5\. Blue Ocean Strategy$',
    '^## 6\. TAM/SAM/SOM$',
    '^## 7\. Jobs-to-be-Done$',
    '^## 8\. Flywheel$',
    '^## 9\. One-Line Pitches$',
    '^## 10\. Honest Weaknesses & Risks$',
    '^## 11\. Monday Morning Actions$'
)

foreach ($pattern in $requiredSections) {
    if (-not ($lines | Where-Object { $_ -match $pattern })) {
        Write-Error "Missing required section matching pattern: $pattern"
        exit 1
    }
}

if ($content -match 'TODO:') {
    Write-Error 'Document still contains TODO placeholders.'
    exit 1
}

if ($lines.Count -lt 120) {
    Write-Error "Expected at least 120 lines for minimum strategic depth, found $($lines.Count)."
    exit 1
}

function Get-SectionLines {
    param(
        [string[]]$AllLines,
        [string]$StartPattern,
        [string]$EndPattern
    )

    $inSection = $false
    $bucket = @()
    foreach ($line in $AllLines) {
        if ($line -match $StartPattern) {
            $inSection = $true
            continue
        }
        if ($inSection -and $line -match $EndPattern) {
            break
        }
        if ($inSection) {
            $bucket += $line
        }
    }
    return $bucket
}

$divergentLines = Get-SectionLines -AllLines $lines -StartPattern '^## 3\. Divergent Ideation' -EndPattern '^## 4\. '
$divergentCount = ($divergentLines | Where-Object { $_ -match '^[0-9]+\. ' }).Count
if ($divergentCount -lt 20) {
    Write-Error "Expected at least 20 divergent ideas, found $divergentCount."
    exit 1
}

$tierCount = ($lines | Where-Object { $_ -match '^#### [SA][0-9]+:' }).Count
if ($tierCount -lt 3) {
    Write-Error "Expected at least 3 detailed Tier S/A entries, found $tierCount."
    exit 1
}

$riskLines = Get-SectionLines -AllLines $lines -StartPattern '^## 10\. Honest Weaknesses & Risks$' -EndPattern '^## 11\. '
$riskDataRows = ($riskLines | Where-Object { $_ -match '^\|[^|]' -and $_ -notmatch '^\|\s*---' -and $_ -notmatch '^\|\s*Weakness\s*\|' }).Count
if ($riskDataRows -lt 5) {
    Write-Error "Expected at least 5 risk rows, found $riskDataRows."
    exit 1
}

$actionLines = Get-SectionLines -AllLines $lines -StartPattern '^## 11\. Monday Morning Actions$' -EndPattern '^$a'
$actionCount = ($actionLines | Where-Object { $_ -match '^[0-9]+\. ' }).Count
if ($actionCount -lt 5) {
    Write-Error "Expected at least 5 Monday Morning actions, found $actionCount."
    exit 1
}

Write-Output 'Brainstorm validation passed'
