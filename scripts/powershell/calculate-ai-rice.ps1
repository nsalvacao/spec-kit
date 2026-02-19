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
    elseif ($e -ge 2) { "MEDIUM (2-5 weeks)" }
    else              { "LOW (<2 weeks)" }
}

function Get-RiskClass([int]$r) {
    if ($r -ge 7)     { "HIGH ($r/10)" }
    elseif ($r -ge 4) { "MEDIUM ($r/10)" }
    else              { "LOW ($r/10)" }
}

function Build-Rationale([int]$r, [double]$i, [int]$c, [int]$dr, [double]$e, [int]$risk) {
    $drivers  = [System.Collections.Generic.List[string]]::new()
    $limiters = [System.Collections.Generic.List[string]]::new()

    # Reach
    if ($r -ge 10000)    { $drivers.Add("very high Reach ($r)") }
    elseif ($r -ge 1000) { $drivers.Add("strong Reach ($r)") }

    # Impact
    if ($i -ge 2.0) { $drivers.Add("$(Get-ImpactClass $i) Impact ($i)") }

    # Confidence
    if ($c -ge 85)      { $drivers.Add("high Confidence (${c}%)") }
    elseif ($c -lt 40)  { $limiters.Add("low Confidence (${c}%)") }

    # Data Readiness
    if ($dr -ge 85)     { $drivers.Add("high Data_Readiness (${dr}%)") }
    elseif ($dr -lt 40) { $limiters.Add("low Data_Readiness (${dr}%)") }

    # Effort
    if ($e -ge 12)    { $limiters.Add("high Effort ($e weeks)") }
    elseif ($e -ge 6) { $limiters.Add("medium Effort ($e weeks)") }

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
Write-Output "Note: To compare across ideas in a session:"
Write-Output "  Norm_Score = (raw_score / session_max_raw) x 100"
