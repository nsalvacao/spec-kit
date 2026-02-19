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

if (-not ($header -match 'Norm_Score')) {
    Write-Error 'AI-RICE scoring table missing Norm_Score column (normalized 0-100 score)'
    if (Test-Path $stateLog) { & $stateLog 'select' 'Framework-Driven Development' 'AI-RICE table missing Norm_Score column' 'high' 'validate-airice' }
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
    if (-not (Select-String -Path $FilePath -Pattern "\*\*$item\*\*:")) {
        Write-Error "Missing dimensional breakdown for $item"
        if (Test-Path $stateLog) { & $stateLog 'select' 'Traceability First' "Missing dimensional breakdown: $item" 'high' 'validate-airice' }
        exit 1
    }
}

# --- Semantic validation: verify formula and value ranges (issue #21) ---
# Parse table data rows: skip header and separator, compute expected AI-RICE score.
$tableLines = Get-Content $FilePath | Where-Object { $_ -match '^\|' }
$dataRows   = $tableLines | Select-Object -Skip 2  # skip header + separator

$semanticErrors = 0

foreach ($row in $dataRows) {
    $cols = $row -split '\|' | ForEach-Object { $_.Trim() }
    # cols[0] is empty (before first |), cols[1]=IdeaID, [2]=Reach, [3]=Impact,
    # [4]=Conf, [5]=DR, [6]=Effort, [7]=Risk, [8]=AI-RICE Score, [9]=Norm_Score
    # Idea ID (cols[1]) may contain link syntax [text](url) — numeric columns need no stripping.
    if ($cols.Count -lt 9) { continue }

    $rawReach  = $cols[2] -replace '[^\d.]', ''
    $rawImpact = $cols[3] -replace '[^\d.]', ''
    $rawConf   = $cols[4] -replace '[^\d.]', ''
    $rawDr     = $cols[5] -replace '[^\d.]', ''
    $rawEffort = $cols[6] -replace '[^\d.]', ''
    $rawRisk   = $cols[7] -replace '[^\d.]', ''
    $storedStr = $cols[8] -replace '[^\d.]', ''

    # Skip placeholder rows (any non-numeric value)
    $allVals = @($rawReach, $rawImpact, $rawConf, $rawDr, $rawEffort, $rawRisk, $storedStr)
    $skip = $false
    foreach ($v in $allVals) {
        if (-not ($v -match '^\d+\.?\d*$')) { $skip = $true; break }
    }
    if ($skip) { continue }

    $r   = [double]$rawReach
    $i   = [double]$rawImpact
    $c   = [double]$rawConf
    $dr  = [double]$rawDr
    $e   = [double]$rawEffort
    $rsk = [double]$rawRisk
    $stored = [double]$storedStr

    # Validate ranges
    if ($c -lt 0 -or $c -gt 100) {
        Write-Error "Error: CONFIDENCE out of range (0-100): $c in row: $row"
        $semanticErrors++
        continue
    }
    if ($dr -lt 0 -or $dr -gt 100) {
        Write-Error "Error: DATA_READINESS out of range (0-100): $dr in row: $row"
        $semanticErrors++
        continue
    }
    if ($rsk -lt 1 -or $rsk -gt 10) {
        Write-Error "Error: RISK out of range (1-10): $rsk in row: $row"
        $semanticErrors++
        continue
    }
    if ($e -le 0) {
        Write-Error "Error: EFFORT must be positive: $e in row: $row"
        $semanticErrors++
        continue
    }

    # Verify formula
    $expected = ($r * $i * $c * $dr) / ($e * $rsk)
    $diff     = [Math]::Abs($expected - $stored)
    if ($diff -gt 0.5) {
        Write-Error ("Error: AI-RICE formula mismatch: expected={0:F2} stored={1:F2} for row (R={2} I={3} C={4}% DR={5}% E={6} Risk={7})" `
            -f $expected, $stored, $r, $i, $c, $dr, $e, $rsk)
        $semanticErrors++
    }
}

if ($semanticErrors -gt 0) {
    if (Test-Path $stateLog) { & $stateLog 'select' 'Framework-Driven Development' "AI-RICE semantic validation failed ($semanticErrors errors)" 'high' 'validate-airice' }
    exit 1
}

Write-Output 'AI-RICE validation passed'
