# brainstorm.ps1 — Strategy pre-phase scaffold for strategic brainstorm artifact.

param(
    [string]$ProjectDir = '',
    [switch]$Force,
    [switch]$Help
)

if ($Help) {
    Write-Output 'Usage: brainstorm.ps1 [[-ProjectDir] <path>] [-Force] [-Help]'
    Write-Output ''
    Write-Output 'Scaffold .ideas/brainstorm-expansion.md for strategic brainstorm.'
    Write-Output ''
    Write-Output 'Arguments:'
    Write-Output '  ProjectDir    Target project directory (default: current directory)'
    Write-Output ''
    Write-Output 'Options:'
    Write-Output '  -Force        Overwrite existing brainstorm-expansion.md'
    Write-Output '  -Help         Show this help message'
    Write-Output ''
    Write-Output 'Next steps after running:'
    Write-Output '  1. Fill all TODO fields in .ideas/brainstorm-expansion.md'
    Write-Output '  2. Keep at least 20 divergent ideas and 5 risks'
    Write-Output '  3. Validate: scripts/powershell/validate-brainstorm.ps1 .ideas/brainstorm-expansion.md'
    exit 0
}

if (-not $ProjectDir) {
    $ProjectDir = (Get-Location).Path
}

if (-not (Test-Path $ProjectDir -PathType Container)) {
    Write-Error "Error: Project directory does not exist: $ProjectDir"
    exit 1
}

$ProjectDir = (Resolve-Path $ProjectDir).Path
$ProjectName = Split-Path -Leaf $ProjectDir
$ideasDir = Join-Path $ProjectDir '.ideas'
$target = Join-Path $ideasDir 'brainstorm-expansion.md'
$timestamp = (Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ')

if ((Test-Path $target -PathType Container)) {
    Write-Error "Error: $target is a directory, not a file. Remove it manually before proceeding."
    exit 1
}

if ((Test-Path $target) -and -not $Force) {
    Write-Error "Error: $target already exists. Use -Force to overwrite."
    exit 1
}

New-Item -ItemType Directory -Force -Path $ideasDir | Out-Null

$content = @"
---
artifact: brainstorm_expansion
phase: strategy
schema_version: "1.0"
generated: $timestamp
derived_from: null
enables: .spec-kit/ideas_backlog.md
---

# $ProjectName — Strategic Brainstorm

**Date:** $timestamp
**Objective:** TODO: Define the strategic objective in one line.

---

## 1. What Is the REAL Asset?

TODO: Explain code vs concept vs moat with one key insight.

## 2. SCAMPER Analysis

### S — Substitute
TODO: Add substitutions with concrete opportunities.

### C — Combine
TODO: Add combinations that create differentiated value.

### A — Adapt
TODO: Add adjacent domains/personas worth adapting to.

### M — Modify / Magnify
TODO: Add 10x scope/depth/intelligence scenarios.

### P — Put to Other Uses
TODO: Add non-obvious applications.

### E — Eliminate
TODO: Add constraints/dependencies to remove.

### R — Reverse / Rearrange
TODO: Add inversion/reordering opportunities.

## 3. Divergent Ideation — 20 Wild Ideas

1. TODO: Idea 01
2. TODO: Idea 02
3. TODO: Idea 03
4. TODO: Idea 04
5. TODO: Idea 05
6. TODO: Idea 06
7. TODO: Idea 07
8. TODO: Idea 08
9. TODO: Idea 09
10. TODO: Idea 10
11. TODO: Idea 11
12. TODO: Idea 12
13. TODO: Idea 13
14. TODO: Idea 14
15. TODO: Idea 15
16. TODO: Idea 16
17. TODO: Idea 17
18. TODO: Idea 18
19. TODO: Idea 19
20. TODO: Idea 20

## 4. Convergent Analysis — Tier Ranking

### Tier S — Transformative (100k+ potential)

#### S1: TODO: Transformative initiative 1
TODO: What, why huge, path, comparable, risk, effort.

### Tier A — High Impact (10k-50k potential)

#### A1: TODO: High-impact initiative 1
TODO: What, why huge, path, comparable, risk, effort.

### Tier B — Strong (1k-10k potential)

TODO: Add at least 3 strong near-term options.

## 5. Blue Ocean Strategy

### Current Market (Red Ocean)
TODO: Add competitor table with real weaknesses.

### Blue Ocean Opportunity
TODO: Add strategic canvas and positioning statement.

## 6. TAM/SAM/SOM

TODO: Add market sizing table and key insight.

## 7. Jobs-to-be-Done

TODO: Add 3-4 persona job statements (functional/emotional/social).

## 8. Flywheel

TODO: Add ASCII flywheel, push point, and friction points.

## 9. One-Line Pitches

1. TODO: For developers
2. TODO: For enterprises
3. TODO: For AI companies
4. TODO: For investors
5. TODO: For CLI/tool authors

## 10. Honest Weaknesses & Risks

| Weakness | Severity | Probability | Mitigation |
| --- | --- | --- | --- |
| TODO: Risk 1 | High | Medium | TODO |
| TODO: Risk 2 | Medium | Medium | TODO |
| TODO: Risk 3 | Medium | Low | TODO |
| TODO: Risk 4 | High | High | TODO |
| TODO: Risk 5 | Low | Medium | TODO |

## 11. Monday Morning Actions

1. TODO: Highest-leverage action 1
2. TODO: Highest-leverage action 2
3. TODO: Highest-leverage action 3
4. TODO: Highest-leverage action 4
5. TODO: Highest-leverage action 5
"@

Set-Content -Path $target -Value $content -Encoding UTF8
Write-Output "Created: $target"
Write-Output ''
Write-Output 'Next steps:'
Write-Output '  1. Fill all TODO fields'
Write-Output '  2. Keep at least 20 divergent ideas, 3+ S/A entries, and 5+ risks'
Write-Output "  3. Validate: scripts/powershell/validate-brainstorm.ps1 $target"
