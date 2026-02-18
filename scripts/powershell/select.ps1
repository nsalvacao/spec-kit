# select.ps1 — Phase 0 SELECT: scaffold idea_selection.md
#
# Creates .spec-kit/idea_selection.md from the standard AI-RICE template.
# Run this after completing Phase 0 IDEATE to score and select ideas.
#
# Usage:
#   .\select.ps1 [[-ProjectDir] <path>] [-Force] [-Help]
#
# Examples:
#   .\select.ps1
#   .\select.ps1 C:\MyProject
#   .\select.ps1 -Force

param(
    [string]$ProjectDir = '',
    [switch]$Force,
    [switch]$Help
)

if ($Help) {
    Write-Output 'Usage: select.ps1 [[-ProjectDir] <path>] [-Force] [-Help]'
    Write-Output ''
    Write-Output 'Scaffold .spec-kit/idea_selection.md for Phase 0 selection (AI-RICE scoring).'
    Write-Output ''
    Write-Output 'Arguments:'
    Write-Output '  ProjectDir    Target project directory (default: current directory)'
    Write-Output ''
    Write-Output 'Options:'
    Write-Output '  -Force        Overwrite existing idea_selection.md'
    Write-Output '  -Help         Show this help message'
    Write-Output ''
    Write-Output 'Prerequisites:'
    Write-Output '  - .spec-kit/ideas_backlog.md must exist (run ideate.ps1 first)'
    Write-Output '  - ideas_backlog.md must pass validate-scamper.ps1'
    Write-Output ''
    Write-Output 'Next steps after running:'
    Write-Output '  1. Open .spec-kit/idea_selection.md and fill in AI-RICE scores'
    Write-Output '  2. AI-RICE formula: (Reach * Impact * Confidence * Data_Readiness) / (Effort * Risk)'
    Write-Output '  3. Normalise scores: best idea = 100, others relative'
    Write-Output '  4. Run: validate-airice.ps1 .spec-kit/idea_selection.md'
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
$specKitDir = Join-Path $ProjectDir '.spec-kit'
$target = Join-Path $specKitDir 'idea_selection.md'
$timestamp = (Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ')

# Check idempotency
if ((Test-Path $target) -and -not $Force) {
    Write-Error "Error: $target already exists. Use -Force to overwrite."
    exit 1
}

# Create .spec-kit directory
New-Item -ItemType Directory -Force -Path $specKitDir | Out-Null

# Write scaffolded idea_selection.md
$content = @"
---
artifact: idea_selection
phase: select
schema_version: "1.0"
generated: $timestamp
ideas_evaluated: 0
selected_idea_id: TBD
derived_from: .spec-kit/ideas_backlog.md
enables: .spec-kit/ai_vision_canvas.md
---

# Idea Selection Report

**Generated**: $timestamp
**Ideas Evaluated**: 0
**Source Backlog**: [ideas_backlog.md](.spec-kit/ideas_backlog.md)

<!--
Guidance:

- AI-RICE is based on RICE (Reach, Impact, Confidence, Effort).
- AI-RICE adds Data_Readiness and Risk.
- Idea IDs in the table MUST link to the corresponding heading anchor in ideas_backlog.md.
- Input dimension guidelines:
  - Reach: number of users/sessions impacted per quarter. Examples: 100 (niche), 1000 (small), 10000 (medium).
  - Impact: 0.25 (minimal), 0.5 (low), 1.0 (normal), 2.0 (high), 3.0 (massive).
  - Confidence: 0-100% (enter as integer percentage, e.g. 70%).
  - Data_Readiness: 0-100% (enter as integer percentage).
  - Effort: person-weeks. Examples: 1 (days), 4 (1 month), 12 (1 quarter).
  - Risk: 1-10 (higher = riskier). 1-3 low, 4-6 medium, 7-10 high.
- Norm_Score = (AI-RICE_raw / session_max_raw) * 100, rounded to 1 decimal.
- Score interpretation: 70-100 = Strong; 40-69 = Viable; 0-39 = Weak.
-->

## AI-RICE Scoring Table

| Idea ID | Reach | Impact | Confidence | Data_Readiness | Effort | Risk | AI-RICE Score | Norm_Score |
| ------- | ----- | ------ | ---------- | -------------- | ------ | ---- | ------------- | ---------- |
| [S1](.spec-kit/ideas_backlog.md#idea-s1) | 0 | 1.0 | 0% | 0% | 1 | 5 | 0.0 | 0.0 |
| [S2](.spec-kit/ideas_backlog.md#idea-s2) | 0 | 1.0 | 0% | 0% | 1 | 5 | 0.0 | 0.0 |

**Formula**: (Reach \* Impact \* Confidence \* Data_Readiness) / (Effort \* Risk)

**Normalization**: Norm\_Score = (AI-RICE\_raw / session\_max\_raw) x 100

## Selected Idea

**ID**: [TBD](.spec-kit/ideas_backlog.md#idea-tbd)
**Text**: [Description of the selected idea]
**Tag**: [SEED | SCAMPER-<Lens> | HMW-<Dimension>]
**AI-RICE Score**: 0.0 (Norm: 0.0/100)

### Dimensional Breakdown

- **Reach**: 0 - [rationale]
- **Impact**: 1.0 - [rationale]
- **Confidence**: 0% - [rationale]
- **Data_Readiness**: 0% - [rationale]
- **Effort**: 1 - [rationale]
- **Risk**: 5 - [rationale]

## Selection Rationale

[Why this idea scored highest; trade-offs vs runner-ups.]

## Runner-Ups (Pivot Options)

### 2nd Place: [IDEA_ID](.spec-kit/ideas_backlog.md#idea-tbd)

- **AI-RICE Score**: 0.0
- **Why Not Selected**: [Reason]
- **Pivot Trigger**: [Condition that would make this the preferred choice]
"@

Set-Content -Path $target -Value $content -Encoding UTF8
Write-Output "Created: $target"
Write-Output ''
Write-Output 'Next steps:'
Write-Output "  1. Open $target and fill in AI-RICE scores for each idea"
Write-Output '  2. Formula: (Reach * Impact * Confidence * Data_Readiness) / (Effort * Risk)'
Write-Output '  3. Normalise scores relative to session maximum'
Write-Output "  4. Validate: scripts/powershell/validate-airice.ps1 $target"
