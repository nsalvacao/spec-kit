$stateDir = '.spec-kit'
$stateFile = Join-Path $stateDir 'state.yaml'

if (-not (Test-Path $stateDir)) {
    New-Item -ItemType Directory -Path $stateDir | Out-Null
}

if (-not (Test-Path $stateFile)) {
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
    Write-Output 'state.yaml initialized'
} else {
    Write-Output 'state.yaml already exists'
}
