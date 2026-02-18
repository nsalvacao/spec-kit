# structure.ps1 — Phase 0 STRUCTURE: scaffold ai_vision_canvas.md
#
# Creates .spec-kit/ai_vision_canvas.md from the standard AI System Vision Canvas template.
# Run this after completing Phase 0 SELECT to structure the chosen idea.
#
# Usage:
#   .\structure.ps1 [[-ProjectDir] <path>] [-Force] [-Help]
#
# Examples:
#   .\structure.ps1
#   .\structure.ps1 C:\MyProject
#   .\structure.ps1 -Force

param(
    [string]$ProjectDir = '',
    [switch]$Force,
    [switch]$Help
)

if ($Help) {
    Write-Output 'Usage: structure.ps1 [[-ProjectDir] <path>] [-Force] [-Help]'
    Write-Output ''
    Write-Output 'Scaffold .spec-kit/ai_vision_canvas.md for Phase 0 structure (AI System Vision Canvas).'
    Write-Output ''
    Write-Output 'Arguments:'
    Write-Output '  ProjectDir    Target project directory (default: current directory)'
    Write-Output ''
    Write-Output 'Options:'
    Write-Output '  -Force        Overwrite existing ai_vision_canvas.md'
    Write-Output '  -Help         Show this help message'
    Write-Output ''
    Write-Output 'Prerequisites:'
    Write-Output '  - .spec-kit/idea_selection.md must exist (run select.ps1 first)'
    Write-Output '  - idea_selection.md must pass validate-airice.ps1'
    Write-Output ''
    Write-Output 'Next steps after running:'
    Write-Output '  1. Open .spec-kit/ai_vision_canvas.md and complete all 18 sections'
    Write-Output '  2. Sections: JTBD (1-5), Lean Startup (6-11), AI-Specific (12-18)'
    Write-Output '  3. Run: validate-canvas.ps1 .spec-kit/ai_vision_canvas.md'
    exit 0
}

# Default to current directory
if (-not $ProjectDir) {
    $ProjectDir = (Get-Location).Path
}

# Validate project directory
if (-not (Test-Path $ProjectDir -PathType Container)) {
    Write-Error "Error: Project directory does not exist: $ProjectDir"
    exit 1
}

$ProjectDir = (Resolve-Path $ProjectDir).Path
$ProjectName = Split-Path -Leaf $ProjectDir
$specKitDir = Join-Path $ProjectDir '.spec-kit'
$target = Join-Path $specKitDir 'ai_vision_canvas.md'
$timestamp = (Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ')

# Check idempotency
if ((Test-Path $target) -and -not $Force) {
    Write-Error "Error: $target already exists. Use -Force to overwrite."
    exit 1
}

# Create .spec-kit directory
New-Item -ItemType Directory -Force -Path $specKitDir | Out-Null

# Write scaffolded ai_vision_canvas.md
$content = @"
---
artifact: ai_vision_canvas
phase: structure
schema_version: "1.0"
generated: $timestamp
selected_idea_id: TBD
derived_from: .spec-kit/idea_selection.md
enables: .spec-kit/vision_brief.md
---

# AI System Vision Canvas: $ProjectName

**Generated**: $timestamp
**Selected Idea**: TBD - [Short label of selected idea]

<!--
Guidance:

- JTBD (Jobs to Be Done) frames the user's progress in context (job statement + outcomes).
- Lean Startup emphasizes hypotheses and validated learning (Build-Measure-Learn).
- AI Risk Management should cover safety, transparency, robustness, and evaluation readiness.
-->

## SECTION 1: JOBS-TO-BE-DONE (5 components)

### 1. Job Statement (When/Want/So)

**When** [situation], **I want** [motivation], **so I can** [outcome].

### 2. Job Executor

Who performs the job? (role/persona)

### 3. Job Context

Where/when does this job occur? Constraints and environment.

### 4. Desired Outcomes

List measurable functional, emotional, and social outcomes.

### 5. Current Solution Pains

What is inadequate today? Where does the current approach fail?

---

## SECTION 2: LEAN STARTUP (6 components)

### 6. Top 3 Problems

The three most critical problems to solve.

### 7. Solution (High-Level)

Describe the solution approach (no tech stack yet).

### 8. Key Assumptions (Critical, Unvalidated)

List hypotheses that must be validated.

### 9. Validation Methods (Build-Measure-Learn)

For each assumption, define how you will test and measure.

### 10. Key Metrics (Success Criteria)

Define measurable indicators of success.

### 11. Cost Structure (Budget Constraints)

Budget, time constraints, and cost drivers.

---

## SECTION 3: AI-SPECIFIC (7 components)

### 12. AI Task

What does the AI predict, classify, generate, or decide?

### 13. Data Requirements

Sources, volume, quality, labeling needs, privacy constraints.

### 14. Model Approach

Model family, prompting strategy, and rationale (high level).

### 15. Evaluation Strategy

Metrics, benchmarks, and human review plan.

### 16. Safety & Risk

Primary risks, mitigations, and trustworthiness considerations.

### 17. Constraints

Latency, cost, compliance, context limits.

### 18. Infrastructure (High-Level)

Hosting, serving infrastructure, and integration points.
"@

Set-Content -Path $target -Value $content -Encoding UTF8
Write-Output "Created: $target"
Write-Output ''
Write-Output 'Next steps:'
Write-Output "  1. Open $target and complete all 18 canvas sections"
Write-Output '  2. SECTION 1: Jobs-to-be-Done (sections 1-5)'
Write-Output '  3. SECTION 2: Lean Startup (sections 6-11)'
Write-Output '  4. SECTION 3: AI-Specific (sections 12-18)'
Write-Output "  5. Validate: scripts/powershell/validate-canvas.ps1 $target"
