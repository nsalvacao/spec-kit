<#
.SYNOPSIS
    AI-RICE score calculator for Phase 0 SELECT.

.DESCRIPTION
    Computes the AI-RICE score from six input dimensions and outputs a
    structured analysis with dimensional breakdown and rationale.

    Formula: (Reach * Impact * Confidence * Data_Readiness) / (Effort * Risk)
    Confidence and Data_Readiness are raw integers 0-100 (percentage values).

.PARAMETER Reach
    Users/sessions impacted per quarter (positive integer).

.PARAMETER Impact
    Impact multiplier: 0.25 | 0.5 | 1.0 | 2.0 | 3.0

.PARAMETER Confidence
    Confidence as integer percentage 0-100.

.PARAMETER DataReadiness
    Data readiness as integer percentage 0-100.

.PARAMETER Effort
    Effort in person-weeks (positive number).

.PARAMETER Risk
    Risk level 1-10 (integer).

.PARAMETER Name
    Optional idea name for display.

.PARAMETER Help
    Show usage and exit.

.EXAMPLE
    .\calculate-ai-rice.ps1 1000 2.0 70 80 4 5 -Name "My Feature"
#>
param(
    [Parameter(Position = 0)][string]$Reach        = "",
    [Parameter(Position = 1)][string]$Impact       = "",
    [Parameter(Position = 2)][string]$Confidence   = "",
    [Parameter(Position = 3)][string]$DataReadiness = "",
    [Parameter(Position = 4)][string]$Effort       = "",
    [Parameter(Position = 5)][string]$Risk         = "",
    [string]$Name = "",
    [switch]$Help
)

if ($Help) {
    Write-Output "Usage: .\calculate-ai-rice.ps1 REACH IMPACT CONFIDENCE DATA_READINESS EFFORT RISK [-Name 'Name']"
    Write-Output ""
    Write-Output "Compute AI-RICE score for a single idea."
    Write-Output ""
    Write-Output "Arguments:"
    Write-Output "  REACH           Users/sessions per quarter (positive integer)"
    Write-Output "  IMPACT          Impact multiplier: 0.25 | 0.5 | 1.0 | 2.0 | 3.0"
    Write-Output "  CONFIDENCE      Confidence percentage 0-100"
    Write-Output "  DATA_READINESS  Data readiness percentage 0-100"
    Write-Output "  EFFORT          Person-weeks (positive number)"
    Write-Output "  RISK            Risk 1-10 (integer)"
    Write-Output ""
    Write-Output "Options:"
    Write-Output "  -Name 'Name'   Optional idea name for display"
    Write-Output "  -Help          Show this help message"
    Write-Output ""
    Write-Output "Formula: (Reach x Impact x Confidence x Data_Readiness) / (Effort x Risk)"
    Write-Output ""
    Write-Output "Example:"
    Write-Output "  .\calculate-ai-rice.ps1 1000 2.0 70 80 4 5 -Name 'My Feature'"
    exit 0
}

# --- Validate all 6 positional args are provided ---
$required = @($Reach, $Impact, $Confidence, $DataReadiness, $Effort, $Risk)
foreach ($arg in $required) {
    if ([string]::IsNullOrWhiteSpace($arg)) {
        Write-Error "Error: Expected 6 positional arguments. Run with -Help for usage."
        exit 1
    }
}

# --- Parse and validate Reach ---
if (-not ($Reach -match '^\d+$') -or [int]$Reach -le 0) {
    Write-Error "Error: REACH must be a positive integer (got: $Reach)"
    exit 1
}
$reachVal = [int]$Reach

# --- Parse and validate Impact ---
$allowedImpact = @('0.25', '0.5', '1.0', '2.0', '3.0')
if ($Impact -notin $allowedImpact) {
    Write-Error "Error: IMPACT must be one of: 0.25, 0.5, 1.0, 2.0, 3.0 (got: $Impact)"
    exit 1
}
$impactVal = [double]$Impact

# --- Parse and validate Confidence ---
if (-not ($Confidence -match '^\d+$') -or [int]$Confidence -gt 100) {
    Write-Error "Error: CONFIDENCE must be an integer 0-100 (got: $Confidence)"
    exit 1
}
$confVal = [int]$Confidence

# --- Parse and validate DataReadiness ---
if (-not ($DataReadiness -match '^\d+$') -or [int]$DataReadiness -gt 100) {
    Write-Error "Error: DATA_READINESS must be an integer 0-100 (got: $DataReadiness)"
    exit 1
}
$drVal = [int]$DataReadiness

# --- Parse and validate Effort ---
try { $effortVal = [double]$Effort } catch {
    Write-Error "Error: EFFORT must be a positive number (got: $Effort)"
    exit 1
}
if ($effortVal -le 0) {
    Write-Error "Error: EFFORT must be a positive number (got: $Effort)"
    exit 1
}

# --- Parse and validate Risk ---
if (-not ($Risk -match '^\d+$') -or [int]$Risk -lt 1 -or [int]$Risk -gt 10) {
    Write-Error "Error: RISK must be an integer 1-10 (got: $Risk)"
    exit 1
}
$riskVal = [int]$Risk

# --- Calculate ---
$numerator   = $reachVal * $impactVal * $confVal * $drVal
$denominator = $effortVal * $riskVal
$rawScore    = $numerator / $denominator

# --- Classify dimensions ---
function Get-ReachClass([int]$r) {
    if ($r -ge 10000) { "HIGH (>=10000 users/quarter)" }
    elseif ($r -ge 1000) { "MEDIUM (1000-9999)" }
    elseif ($r -ge 100)  { "SMALL (100-999)" }
    else                  { "NICHE (<100)" }
}

function Get-ImpactClass([double]$i) {
    switch ($i) {
        3.0     { "MASSIVE" }
        2.0     { "HIGH" }
        1.0     { "NORMAL" }
        0.5     { "LOW" }
        default { "MINIMAL" }
    }
}

function Get-PctClass([int]$p, [string]$label) {
    if ($p -ge 85)     { "${label}: HIGH (${p}%)" }
    elseif ($p -ge 70) { "${label}: GOOD (${p}%)" }
    elseif ($p -ge 40) { "${label}: MODERATE (${p}%)" }
    else               { "${label}: LOW (${p}%)" }
}

function Get-EffortClass([double]$e) {
    if ($e -ge 12)    { "HIGH (>=12 weeks - quarter)" }
    elseif ($e -ge 6) { "MEDIUM (6-11 weeks)" }
    elseif ($e -ge 2) { "MODERATE (2-5 weeks)" }
    else              { "LOW (<2 weeks)" }
}

function Get-RiskClass([int]$r) {
    if ($r -ge 7)     { "HIGH ($r/10)" }
    elseif ($r -ge 4) { "MEDIUM ($r/10)" }
    else              { "LOW ($r/10)" }
}

function Build-Rationale([int]$r, [double]$i, [int]$c, [int]$dr, [double]$e, [int]$risk) {
    $drivers   = [System.Collections.Generic.List[string]]::new()
    $limiters  = [System.Collections.Generic.List[string]]::new()
    $moderators= [System.Collections.Generic.List[string]]::new()

    # Reach
    if ($r -ge 10000)    { $drivers.Add("very high Reach ($r)") }
    elseif ($r -ge 1000) { $drivers.Add("strong Reach ($r)") }
    elseif ($r -ge 100)  { $moderators.Add("moderate Reach ($r)") }

    # Impact
    if ($i -ge 2.0) { $drivers.Add("$(Get-ImpactClass $i) Impact ($i)") }

    # Confidence
    if ($c -ge 85)      { $drivers.Add("high Confidence (${c}%)") }
    elseif ($c -ge 40)  { $moderators.Add("moderate Confidence (${c}%)") }
    elseif ($c -lt 40)  { $limiters.Add("low Confidence (${c}%)") }

    # Data Readiness
    if ($dr -ge 85)     { $drivers.Add("high Data_Readiness (${dr}%)") }
    elseif ($dr -ge 40) { $moderators.Add("moderate Data_Readiness (${dr}%)") }
    elseif ($dr -lt 40) { $limiters.Add("low Data_Readiness (${dr}%)") }

    # Effort
    if ($e -ge 12)    { $limiters.Add("high Effort ($e weeks)") }
    elseif ($e -ge 6) { $limiters.Add("medium Effort ($e weeks)") }
    elseif ($e -ge 2) { $moderators.Add("moderate Effort ($e weeks)") }
    else              { $moderators.Add("low Effort ($e weeks)") }

    # Risk
    if ($risk -ge 7)     { $limiters.Add("high Risk ($risk/10)") }
    elseif ($risk -ge 4) { $limiters.Add("medium Risk ($risk/10)") }

    $driverStr  = if ($drivers.Count -gt 0)  { "Score driven by $($drivers -join ', ')." } else { "No standout drivers detected." }
    $limiterStr = if ($limiters.Count -gt 0) { " Limited by $($limiters -join ', ')." }    else { "" }
    "$driverStr$limiterStr"
}

$reachClass  = Get-ReachClass  $reachVal
$impactClass = Get-ImpactClass $impactVal
$confClass   = Get-PctClass    $confVal   "Confidence"
$drClass     = Get-PctClass    $drVal     "Data_Readiness"
$effortClass = Get-EffortClass $effortVal
$riskClass   = Get-RiskClass   $riskVal
$rationale   = Build-Rationale $reachVal $impactVal $confVal $drVal $effortVal $riskVal

# --- Sensitivity Analysis ---

$impactScale = @(0.25, 0.5, 1.0, 2.0, 3.0)

function Get-ImpactStepUp([double]$current) {
    $idx = [Array]::IndexOf($impactScale, $current)
    if ($idx -ge 0 -and $idx -lt ($impactScale.Length - 1)) { $impactScale[$idx + 1] } else { $current }
}

function Get-ImpactStepDown([double]$current) {
    $idx = [Array]::IndexOf($impactScale, $current)
    if ($idx -gt 0) { $impactScale[$idx - 1] } else { $current }
}

function Get-ScoreRaw([double]$r, [double]$i, [double]$c, [double]$dr, [double]$e, [double]$risk) {
    [math]::Round(($r * $i * $c * $dr) / ($e * $risk), 2)
}

function Format-Delta([double]$newScore, [double]$base) {
    $d = $newScore - $base
    if ($d -ge 0) { "+{0:F2}" -f $d } else { "{0:F2}" -f $d }
}

function Clamp-Pct([int]$v)  { [math]::Max(0,  [math]::Min(100, $v)) }
function Clamp-Risk([int]$v) { [math]::Max(1,  [math]::Min(10,  $v)) }
function Clamp-Reach([int]$v){ [math]::Max(1,  $v) }

# Bounded +-1 values per dimension
$sensRP = Clamp-Reach ($reachVal + 1)
$sensRM = Clamp-Reach ($reachVal - 1)
$sensIP = Get-ImpactStepUp   $impactVal
$sensIM = Get-ImpactStepDown $impactVal
$sensCP = Clamp-Pct ($confVal + 1)
$sensCM = Clamp-Pct ($confVal - 1)
$sensDP = Clamp-Pct ($drVal + 1)
$sensDM = Clamp-Pct ($drVal - 1)
$sensEP = $effortVal + 1
$sensEM = [math]::Max(1.0, $effortVal - 1)
$sensKP = Clamp-Risk ($riskVal + 1)
$sensKM = Clamp-Risk ($riskVal - 1)

# Scenario scores
$scRP = Get-ScoreRaw $sensRP  $impactVal $confVal  $drVal    $effortVal $riskVal
$scRM = Get-ScoreRaw $sensRM  $impactVal $confVal  $drVal    $effortVal $riskVal
$scIP = Get-ScoreRaw $reachVal $sensIP   $confVal  $drVal    $effortVal $riskVal
$scIM = Get-ScoreRaw $reachVal $sensIM   $confVal  $drVal    $effortVal $riskVal
$scCP = Get-ScoreRaw $reachVal $impactVal $sensCP  $drVal    $effortVal $riskVal
$scCM = Get-ScoreRaw $reachVal $impactVal $sensCM  $drVal    $effortVal $riskVal
$scDP = Get-ScoreRaw $reachVal $impactVal $confVal $sensDP   $effortVal $riskVal
$scDM = Get-ScoreRaw $reachVal $impactVal $confVal $sensDM   $effortVal $riskVal
$scEP = Get-ScoreRaw $reachVal $impactVal $confVal $drVal    $sensEP    $riskVal
$scEM = Get-ScoreRaw $reachVal $impactVal $confVal $drVal    $sensEM    $riskVal
$scKP = Get-ScoreRaw $reachVal $impactVal $confVal $drVal    $effortVal $sensKP
$scKM = Get-ScoreRaw $reachVal $impactVal $confVal $drVal    $effortVal $sensKM

# Delta strings
$dRP = Format-Delta $scRP $rawScore; $dRM = Format-Delta $scRM $rawScore
$dIP = Format-Delta $scIP $rawScore; $dIM = Format-Delta $scIM $rawScore
$dCP = Format-Delta $scCP $rawScore; $dCM = Format-Delta $scCM $rawScore
$dDP = Format-Delta $scDP $rawScore; $dDM = Format-Delta $scDM $rawScore
$dEP = Format-Delta $scEP $rawScore; $dEM = Format-Delta $scEM $rawScore
$dKP = Format-Delta $scKP $rawScore; $dKM = Format-Delta $scKM $rawScore

# Identify best positive and negative levers
$posScenarios = @(
    @{name="Reach +1";          delta=$scRP - $rawScore},
    @{name="Impact +1 step";    delta=$scIP - $rawScore},
    @{name="Confidence +1%";    delta=$scCP - $rawScore},
    @{name="Data_Readiness +1%";delta=$scDP - $rawScore},
    @{name="Effort -1 wk";      delta=$scEM - $rawScore},
    @{name="Risk -1";           delta=$scKM - $rawScore}
)
$negScenarios = @(
    @{name="Reach -1";          delta=$scRM - $rawScore},
    @{name="Impact -1 step";    delta=$scIM - $rawScore},
    @{name="Confidence -1%";    delta=$scCM - $rawScore},
    @{name="Data_Readiness -1%";delta=$scDM - $rawScore},
    @{name="Effort +1 wk";      delta=$scEP - $rawScore},
    @{name="Risk +1";           delta=$scKP - $rawScore}
)
$bestPos = $posScenarios | Sort-Object { $_.delta } -Descending | Select-Object -First 1
$bestNeg = $negScenarios | Sort-Object { $_.delta } | Select-Object -First 1
$bestPosDStr = if ($bestPos.delta -ge 0) { "+{0:F2}" -f $bestPos.delta } else { "{0:F2}" -f $bestPos.delta }
$bestNegDStr = "{0:F2}" -f $bestNeg.delta

# --- Output ---
Write-Output "+-------------------------------------------------------------+"
if ($Name) {
    Write-Output ("| AI-RICE Calculator -- {0,-40}|" -f $Name)
} else {
    Write-Output "| AI-RICE Calculator                                          |"
}
Write-Output "+-------------------------------------------------------------+"
Write-Output ""
Write-Output "Input Dimensions:"
Write-Output ("  {0,-20} {1}" -f "Reach:",         "$reachVal ($reachClass)")
Write-Output ("  {0,-20} {1}" -f "Impact:",        "$impactVal ($impactClass)")
Write-Output ("  {0,-20} {1}" -f "Confidence:",    "${confVal}% ($confClass)")
Write-Output ("  {0,-20} {1}" -f "Data_Readiness:","${drVal}% ($drClass)")
Write-Output ("  {0,-20} {1}" -f "Effort:",        "$effortVal weeks ($effortClass)")
Write-Output ("  {0,-20} {1}" -f "Risk:",          "$riskVal/10 ($riskClass)")
Write-Output ""
Write-Output "Formula: (Reach x Impact x Confidence x Data_Readiness) / (Effort x Risk)"
Write-Output "       = ($reachVal x $impactVal x $confVal x $drVal) / ($effortVal x $riskVal)"
Write-Output ("       = {0:F0} / {1:F0}" -f $numerator, $denominator)
Write-Output ""
Write-Output ("AI-RICE Raw Score: {0:F2}" -f $rawScore)
Write-Output ""
Write-Output "Dimensional Analysis:"
Write-Output "  ^ Numerator (amplifiers): Reach, Impact, Confidence, Data_Readiness"
Write-Output "  v Denominator (reducers):  Effort, Risk"
Write-Output ""
Write-Output "  Reach          -> $reachClass"
Write-Output "  Impact         -> $impactClass ($impactVal)"
Write-Output "  $confClass"
Write-Output "  $drClass"
Write-Output "  Effort         -> $effortClass"
Write-Output "  Risk           -> $riskClass"
Write-Output ""
Write-Output "Rationale: $rationale"
Write-Output ""
Write-Output "Sensitivity Analysis (what-if +-1 per dimension):"
Write-Output ("  {0,-18} +1 -> {1} (D{2}) | -1 -> {3} (D{4})" -f "Reach:", $scRP, $dRP, $scRM, $dRM)
Write-Output ("  {0,-18} +1 step -> {1} (D{2}) | -1 step -> {3} (D{4})" -f "Impact:", $scIP, $dIP, $scIM, $dIM)
Write-Output ("  {0,-18} +1% -> {1} (D{2}) | -1% -> {3} (D{4})" -f "Confidence:", $scCP, $dCP, $scCM, $dCM)
Write-Output ("  {0,-18} +1% -> {1} (D{2}) | -1% -> {3} (D{4})" -f "Data_Readiness:", $scDP, $dDP, $scDM, $dDM)
Write-Output ("  {0,-18} +1 wk -> {1} (D{2}) | -1 wk -> {3} (D{4})" -f "Effort:", $scEP, $dEP, $scEM, $dEM)
Write-Output ("  {0,-18} +1 -> {1} (D{2}) | -1 -> {3} (D{4})" -f "Risk:", $scKP, $dKP, $scKM, $dKM)
Write-Output ""
Write-Output "Levers summary:"
Write-Output "  ^ Best upside:  $($bestPos.name) -> D$bestPosDStr"
Write-Output "  v Biggest risk: $($bestNeg.name) -> D$bestNegDStr"
Write-Output ""
Write-Output "Note: To compare across ideas in a session:"
Write-Output "  Norm_Score = (raw_score / session_max_raw) x 100"
