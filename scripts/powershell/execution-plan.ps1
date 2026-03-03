# execution-plan.ps1 - Strategy planning scaffold for execution-plan artifact.

param(
    [string]$ProjectDir = '',
    [switch]$Force,
    [switch]$Help
)

if ($Help) {
    Write-Output 'Usage: execution-plan.ps1 [[-ProjectDir] <path>] [-Force] [-Help]'
    Write-Output ''
    Write-Output 'Scaffold .ideas/execution-plan.md for strategic execution planning.'
    Write-Output ''
    Write-Output 'Arguments:'
    Write-Output '  ProjectDir    Target project directory (default: current directory)'
    Write-Output ''
    Write-Output 'Options:'
    Write-Output '  -Force        Overwrite existing execution-plan.md'
    Write-Output '  -Help         Show this help message'
    Write-Output ''
    Write-Output 'Next steps after running:'
    Write-Output '  1. Fill all TODO fields in .ideas/execution-plan.md'
    Write-Output '  2. Complete all mandatory sections and tables'
    Write-Output '  3. Validate: scripts/powershell/validate-execution-plan.ps1 .ideas/execution-plan.md'
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
$target = Join-Path $ideasDir 'execution-plan.md'
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
artifact: execution_plan
phase: strategy
schema_version: "1.0"
generated: $timestamp
derived_from: .ideas/brainstorm-expansion.md
enables: .ideas/evaluation-results.md
---

# $ProjectName - Strategic Execution Plan

**Date:** $timestamp
**Status:** Draft v1.0
**Objective:** TODO: Define the execution objective in one sentence.

---

## Table of Contents

1. Second-Order Thinking & Anticipation Layer
2. Polish & Improvements Before Public Exposure
3. Expected Impacts Matrix
4. Operationalized Roadmap
4b. Pre-Mortem Analysis
4c. Moat Assessment
5. Risk Register
6. Growth & Visibility Strategy
7. Contrarian Challenges
Appendices

## 1. Second-Order Thinking & Anticipation Layer

### 1.1 Second-Order Effects by Initiative

#### Initiative 1: TODO
| Order | Effect | Implication |
| --- | --- | --- |
| First | TODO | TODO |
| Second | TODO | TODO |
| Third | TODO | TODO |

**Key insight:** TODO

#### Initiative 2: TODO
| Order | Effect | Implication |
| --- | --- | --- |
| First | TODO | TODO |
| Second | TODO | TODO |
| Third | TODO | TODO |

**Key insight:** TODO

#### Initiative 3: TODO
| Order | Effect | Implication |
| --- | --- | --- |
| First | TODO | TODO |
| Second | TODO | TODO |
| Third | TODO | TODO |

**Key insight:** TODO

### 1.2 Failure Modes by Phase

| Phase | Failure mode | Probability | Mitigation |
| --- | --- | --- | --- |
| Phase 1 | TODO | TODO | TODO |
| Phase 2 | TODO | TODO | TODO |
| Phase 3 | TODO | TODO | TODO |
| Phase 4 | TODO | TODO | TODO |

### 1.3 Competitive Responses

TODO: Document likely competitor responses and counter-moves.

### 1.4 Timing Risks

TODO: Document external timing risks and hedges.

### 1.5 Dependencies & Critical Path

TODO: Add dependency map and critical path notes.

## 2. Polish & Improvements Before Public Exposure

### 2.1 Code Quality Audit Checklist

| Area | Status (PASS/PARTIAL/FAIL) | Action Needed | Priority |
| --- | --- | --- | --- |
| Tests | TODO | TODO | TODO |
| Error handling | TODO | TODO | TODO |
| Security | TODO | TODO | TODO |
| CI/CD | TODO | TODO | TODO |
| Documentation | TODO | TODO | TODO |

### 2.2 Documentation Gaps

| Document | Exists (YES/NO) | Action |
| --- | --- | --- |
| README.md | TODO | TODO |
| CONTRIBUTING.md | TODO | TODO |
| CHANGELOG.md | TODO | TODO |
| Architecture docs | TODO | TODO |
| API/CLI docs | TODO | TODO |

### 2.3 README Optimization

TODO: Evaluate first impression, value proposition, and conversion friction.

### 2.4 Demo/GIF/Video Needs

TODO: Define demo assets required pre-launch.

### 2.5 Pre-Launch Evaluation Checkpoint

TODO: Define how evaluation and advanced-evaluation will be invoked before launch.

## 3. Expected Impacts Matrix

| Item | Reach | Effort (days) | Star Impact | Revenue | Moat Contribution |
| --- | --- | --- | --- | --- | --- |
| TODO | TODO | TODO | TODO | TODO | TODO |
| TODO | TODO | TODO | TODO | TODO | TODO |
| TODO | TODO | TODO | TODO | TODO | TODO |
| TODO | TODO | TODO | TODO | TODO | TODO |

## 4. Operationalized Roadmap

### Phase 1: Foundation (TODO timeframe)

#### Track A: TODO

| # | Deliverable | Acceptance Criteria | Days | Quick Win? |
| --- | --- | --- | --- | --- |
| A1 | TODO | TODO | TODO | TODO |
| A2 | TODO | TODO | TODO | TODO |

**Exit criteria:** TODO

### Phase 2: Expansion (TODO timeframe)

#### Track B: TODO

| # | Deliverable | Acceptance Criteria | Days | Quick Win? |
| --- | --- | --- | --- | --- |
| B1 | TODO | TODO | TODO | TODO |
| B2 | TODO | TODO | TODO | TODO |

**Exit criteria:** TODO

### Phase 3: Platform (TODO timeframe)

#### Track C: TODO

| # | Deliverable | Acceptance Criteria | Days | Quick Win? |
| --- | --- | --- | --- | --- |
| C1 | TODO | TODO | TODO | TODO |
| C2 | TODO | TODO | TODO | TODO |

**Exit criteria:** TODO

### Phase 4: Scale (TODO timeframe)

#### Track D: TODO

| # | Deliverable | Acceptance Criteria | Days | Quick Win? |
| --- | --- | --- | --- | --- |
| D1 | TODO | TODO | TODO | TODO |
| D2 | TODO | TODO | TODO | TODO |

**Exit criteria:** TODO

## 4b. Pre-Mortem Analysis

| # | Cause of Death | Category | Probability | Prevention |
| --- | --- | --- | --- | --- |
| 1 | TODO | Technical | TODO | TODO |
| 2 | TODO | Market | TODO | TODO |
| 3 | TODO | Execution | TODO | TODO |
| 4 | TODO | External | TODO | TODO |
| 5 | TODO | Community | TODO | TODO |
| 6 | TODO | Technical | TODO | TODO |
| 7 | TODO | Market | TODO | TODO |
| 8 | TODO | Execution | TODO | TODO |

## 4c. Moat Assessment

| Moat Type | Current | Buildable? | How | Timeline |
| --- | --- | --- | --- | --- |
| Network Effects | TODO | TODO | TODO | TODO |
| Switching Costs | TODO | TODO | TODO | TODO |
| Brand / Trust | TODO | TODO | TODO | TODO |
| Cost Advantage | TODO | TODO | TODO | TODO |

## 5. Risk Register

| # | Risk | Prob. | Impact | Mitigation |
| --- | --- | --- | --- | --- |
| 1 | TODO | TODO | TODO | TODO |
| 2 | TODO | TODO | TODO | TODO |
| 3 | TODO | TODO | TODO | TODO |
| 4 | TODO | TODO | TODO | TODO |
| 5 | TODO | TODO | TODO | TODO |
| 6 | TODO | TODO | TODO | TODO |
| 7 | TODO | TODO | TODO | TODO |
| 8 | TODO | TODO | TODO | TODO |
| 9 | TODO | TODO | TODO | TODO |
| 10 | TODO | TODO | TODO | TODO |

## 6. Growth & Visibility Strategy

### 6.1 Launch Channels

| Channel | Audience size | Timing | Expected impact | Content type |
| --- | --- | --- | --- | --- |
| TODO | TODO | TODO | TODO | TODO |
| TODO | TODO | TODO | TODO | TODO |
| TODO | TODO | TODO | TODO | TODO |

### 6.2 Content Strategy

| Week | Content piece | Channel | Purpose |
| --- | --- | --- | --- |
| 1 | TODO | TODO | TODO |
| 2 | TODO | TODO | TODO |
| 3 | TODO | TODO | TODO |
| 4 | TODO | TODO | TODO |

### 6.3 Community Building

| Mechanism | When | Why |
| --- | --- | --- |
| TODO | TODO | TODO |
| TODO | TODO | TODO |
| TODO | TODO | TODO |

### 6.4 Partnership Opportunities

| Partner type | Targets | Pitch (one line) | Timing |
| --- | --- | --- | --- |
| TODO | TODO | TODO | TODO |
| TODO | TODO | TODO | TODO |

### 6.5 HN Title A/B Testing

1. TODO: Technical angle
2. TODO: Problem-first angle
3. TODO: Analogy angle

### 6.6 Star Growth Model

| Milestone | Target date | Strategy |
| --- | --- | --- |
| TODO | TODO | TODO |
| TODO | TODO | TODO |
| TODO | TODO | TODO |

## 7. Contrarian Challenges

| Assumption | Contrarian View | Prob. Wrong | Hedge |
| --- | --- | --- | --- |
| TODO | TODO | TODO | TODO |
| TODO | TODO | TODO | TODO |
| TODO | TODO | TODO | TODO |
| TODO | TODO | TODO | TODO |
| TODO | TODO | TODO | TODO |

## Appendices

### A. Immediate Action Items (This Week)

1. TODO
2. TODO
3. TODO
4. TODO
5. TODO

### B. Key Files Reference

TODO: List key files and why they matter for the plan.

### C. Quantitative Analysis

TODO: Include quantified assumptions (cost, effort, impact, throughput, risk).
"@

Set-Content -Path $target -Value $content -Encoding UTF8
Write-Output "Created: $target"
Write-Output ''
Write-Output 'Next steps:'
Write-Output '  1. Fill all TODO fields'
Write-Output '  2. Complete all required sections with evidence-backed content'
Write-Output "  3. Validate: scripts/powershell/validate-execution-plan.ps1 $target"
