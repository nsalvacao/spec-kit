$stateDir = '.spec-kit'
$stateFile = Join-Path $stateDir 'state.yaml'

if (-not (Get-Command yq -ErrorAction SilentlyContinue)) {
    Write-Error 'yq not found. Install: https://github.com/mikefarah/yq'
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

if (Test-Path $ideasBacklog) { yq e ".artifacts.ideas_backlog = \"$ideasBacklog\"" $stateFile | Set-Content -Path "$stateDir/.state.yaml.tmp" -NoNewline; Move-Item -Force "$stateDir/.state.yaml.tmp" $stateFile }
if (Test-Path $ideaSelection) { yq e ".artifacts.idea_selection = \"$ideaSelection\"" $stateFile | Set-Content -Path "$stateDir/.state.yaml.tmp" -NoNewline; Move-Item -Force "$stateDir/.state.yaml.tmp" $stateFile }
if (Test-Path $aiVisionCanvas) { yq e ".artifacts.ai_vision_canvas = \"$aiVisionCanvas\"" $stateFile | Set-Content -Path "$stateDir/.state.yaml.tmp" -NoNewline; Move-Item -Force "$stateDir/.state.yaml.tmp" $stateFile }
if (Test-Path $visionBrief) { yq e ".artifacts.vision_brief = \"$visionBrief\"" $stateFile | Set-Content -Path "$stateDir/.state.yaml.tmp" -NoNewline; Move-Item -Force "$stateDir/.state.yaml.tmp" $stateFile }
if (Test-Path $g0Report) { yq e ".artifacts.g0_validation_report = \"$g0Report\"" $stateFile | Set-Content -Path "$stateDir/.state.yaml.tmp" -NoNewline; Move-Item -Force "$stateDir/.state.yaml.tmp" $stateFile }

if ($phasesCompleted.Count -gt 0) {
    $phasesJson = '[' + ($phasesCompleted | ForEach-Object { '"' + $_ + '"' } -join ',') + ']'
    yq e ".phases_completed = $phasesJson | .current_phase = \"$currentPhase\"" $stateFile | Set-Content -Path "$stateDir/.state.yaml.tmp" -NoNewline
    Move-Item -Force "$stateDir/.state.yaml.tmp" $stateFile
}

Write-Output 'state.yaml reconstructed'
