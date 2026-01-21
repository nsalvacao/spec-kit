$stateDir = '.spec-kit'
$stateFile = Join-Path $stateDir 'state.yaml'
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$pythonScript = Join-Path (Split-Path -Parent $scriptDir) 'python/state-update.py'

if (-not (Get-Command python3 -ErrorAction SilentlyContinue)) {
    Write-Error 'python3 not found. Please install Python 3'
    exit 1
}

if (-not (Test-Path $stateDir)) {
    New-Item -ItemType Directory -Path $stateDir | Out-Null
}

$ideasBacklog = Join-Path $stateDir 'ideas_backlog.md'
$ideaSelection = Join-Path $stateDir 'idea_selection.md'
$aiVisionCanvas = Join-Path $stateDir 'ai_vision_canvas.md'
$visionBrief = Join-Path $stateDir 'vision_brief.md'
$g0Report = Join-Path (Join-Path $stateDir 'approvals') 'g0-validation-report.md'

$phasesCompleted = @()
$currentPhase = 'ideate'

if (Test-Path $ideasBacklog) { $phasesCompleted += 'ideate'; $currentPhase = 'select' }
if (Test-Path $ideaSelection) { $phasesCompleted += 'select'; $currentPhase = 'structure' }
if ((Test-Path $aiVisionCanvas) -and (Test-Path $visionBrief)) { $phasesCompleted += 'structure'; $currentPhase = 'validate' }
if (Test-Path $g0Report) { $phasesCompleted += 'validate'; $currentPhase = 'validate' }

@'
workflow_version: "1.0"
current_phase: ideate
phases_completed: []
phases_in_progress: []
artifacts:
  ideas_backlog: null
  idea_selection: null
  ai_vision_canvas: null
  vision_brief: null
  g0_validation_report: null
profile: ai-system
violations: []
'@ | Set-Content -Path $stateFile -NoNewline

if (Test-Path $ideasBacklog) { 
    & python3 $pythonScript --file $stateFile --operation set-value --key artifacts.ideas_backlog --value $ideasBacklog
}
if (Test-Path $ideaSelection) { 
    & python3 $pythonScript --file $stateFile --operation set-value --key artifacts.idea_selection --value $ideaSelection
}
if (Test-Path $aiVisionCanvas) { 
    & python3 $pythonScript --file $stateFile --operation set-value --key artifacts.ai_vision_canvas --value $aiVisionCanvas
}
if (Test-Path $visionBrief) { 
    & python3 $pythonScript --file $stateFile --operation set-value --key artifacts.vision_brief --value $visionBrief
}
if (Test-Path $g0Report) { 
    & python3 $pythonScript --file $stateFile --operation set-value --key artifacts.g0_validation_report --value $g0Report
}

if ($phasesCompleted.Count -gt 0) {
    $phasesJson = '[' + ($phasesCompleted | ForEach-Object { '"' + $_ + '"' } -join ',') + ']'
    $jsonData = "{`"phases_completed`": $phasesJson, `"current_phase`": `"$currentPhase`"}"
    & python3 $pythonScript --file $stateFile --operation set-multiple --json-data $jsonData
}

Write-Output 'state.yaml reconstructed'
