param(
    [string]$FilePath = '.ideas/execution-plan.md'
)

if (-not (Test-Path $FilePath)) {
    Write-Error "execution plan document not found at $FilePath"
    exit 1
}

$content = Get-Content -Path $FilePath -Raw -Encoding UTF8
$lines = Get-Content -Path $FilePath -Encoding UTF8

$requiredSections = @(
    '^## 1\. Second-Order Thinking & Anticipation Layer$',
    '^### 1\.1 Second-Order Effects by Initiative$',
    '^### 1\.2 Failure Modes by Phase$',
    '^### 1\.3 Competitive Responses$',
    '^### 1\.4 Timing Risks$',
    '^### 1\.5 Dependencies & Critical Path$',
    '^## 2\. Polish & Improvements Before Public Exposure$',
    '^### 2\.1 Code Quality Audit Checklist$',
    '^### 2\.2 Documentation Gaps$',
    '^### 2\.3 README Optimization$',
    '^### 2\.4 Demo/GIF/Video Needs$',
    '^### 2\.5 Pre-Launch Evaluation Checkpoint$',
    '^## 3\. Expected Impacts Matrix$',
    '^## 4\. Operationalized Roadmap$',
    '^## 4b\. Pre-Mortem Analysis$',
    '^## 4c\. Moat Assessment$',
    '^## 5\. Risk Register$',
    '^## 6\. Growth & Visibility Strategy$',
    '^## 7\. Contrarian Challenges$',
    '^## Appendices$'
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

if ($lines.Count -lt 180) {
    Write-Error "Expected at least 180 lines for minimum strategic depth, found $($lines.Count)."
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

$phaseCount = ($lines | Where-Object { $_ -match '^### Phase [0-9]+:' }).Count
if ($phaseCount -lt 4) {
    Write-Error "Expected at least 4 roadmap phases, found $phaseCount."
    exit 1
}

$preMortemLines = Get-SectionLines -AllLines $lines -StartPattern '^## 4b\. Pre-Mortem Analysis$' -EndPattern '^## 4c\. '
$preMortemRows = ($preMortemLines | Where-Object {
    $_ -match '^\|[^|]' -and
    $_ -notmatch '^\|\s*---' -and
    $_ -notmatch '^\|\s*#\s*\|'
}).Count
if ($preMortemRows -lt 8) {
    Write-Error "Expected at least 8 pre-mortem rows, found $preMortemRows."
    exit 1
}

$riskLines = Get-SectionLines -AllLines $lines -StartPattern '^## 5\. Risk Register$' -EndPattern '^## 6\. '
$riskRows = ($riskLines | Where-Object {
    $_ -match '^\|[^|]' -and
    $_ -notmatch '^\|\s*---' -and
    $_ -notmatch '^\|\s*#\s*\|'
}).Count
if ($riskRows -lt 10) {
    Write-Error "Expected at least 10 risk rows, found $riskRows."
    exit 1
}

$contrarianLines = Get-SectionLines -AllLines $lines -StartPattern '^## 7\. Contrarian Challenges$' -EndPattern '^## Appendices$'
$contrarianRows = ($contrarianLines | Where-Object {
    $_ -match '^\|[^|]' -and
    $_ -notmatch '^\|\s*---' -and
    $_ -notmatch '^\|\s*Assumption\s*\|'
}).Count
if ($contrarianRows -lt 5) {
    Write-Error "Expected at least 5 contrarian challenge rows, found $contrarianRows."
    exit 1
}

Write-Output 'Execution plan validation passed'
