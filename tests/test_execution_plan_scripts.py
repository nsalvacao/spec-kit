"""Tests for strategic execution-plan scaffolding and validation scripts (issue #205)."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

SCRIPT_DIR = Path(__file__).parent.parent / "scripts" / "bash"
PS1_DIR = Path(__file__).parent.parent / "scripts" / "powershell"

EXECUTION_PLAN = SCRIPT_DIR / "execution-plan.sh"
VALIDATE_EXECUTION_PLAN = SCRIPT_DIR / "validate-execution-plan.sh"
EXECUTION_PLAN_PS1 = PS1_DIR / "execution-plan.ps1"
VALIDATE_EXECUTION_PLAN_PS1 = PS1_DIR / "validate-execution-plan.ps1"

PWSH = shutil.which("pwsh")
skip_no_pwsh = pytest.mark.skipif(PWSH is None, reason="pwsh not available")


def run(script: Path, *args, cwd=None) -> subprocess.CompletedProcess:
    return subprocess.run(
        [str(script), *args],
        capture_output=True,
        text=True,
        cwd=cwd,
    )


def run_ps1(script: Path, *args, cwd=None) -> subprocess.CompletedProcess:
    return subprocess.run(
        [PWSH, "-NonInteractive", "-File", str(script), *args],
        capture_output=True,
        text=True,
        cwd=cwd,
    )


def _build_valid_execution_plan(project_name: str = "Demo") -> str:
    impacts = "\n".join(
        f"| Initiative {idx} | {idx * 1000} | {idx * 2} | High | Indirect | Strong |"
        for idx in range(1, 7)
    )

    roadmap_blocks = "\n\n".join(
        (
            f"### Phase {phase}: Stage {phase} (Weeks {phase}-{phase + 1})\n\n"
            f"#### Track {chr(64 + phase)}: Track {phase}\n\n"
            "| # | Deliverable | Acceptance Criteria | Days | Quick Win? |\n"
            "| --- | --- | --- | --- | --- |\n"
            f"| {chr(64 + phase)}1 | Deliverable {phase}.1 | Measurable acceptance criteria for {phase}.1 | {phase + 1} | No |\n"
            f"| {chr(64 + phase)}2 | Deliverable {phase}.2 | Measurable acceptance criteria for {phase}.2 | {phase + 2} | Yes |\n\n"
            f"**Exit criteria:** Exit condition for phase {phase}."
        )
        for phase in range(1, 5)
    )

    pre_mortem_rows = "\n".join(
        f"| {idx} | Failure mode {idx} | {'Technical' if idx % 2 else 'Market'} | {10 + idx}% | Mitigation path {idx} |"
        for idx in range(1, 9)
    )

    moat_rows = "\n".join(
        f"| {moat} | Medium | Yes | Build strategy for {moat.lower()} | 6 months |"
        for moat in ["Network Effects", "Switching Costs", "Brand / Trust", "Cost Advantage"]
    )

    risk_rows = "\n".join(
        f"| {idx} | Risk item {idx} | {10 + idx}% | High | Mitigation item {idx} with owner and date |"
        for idx in range(1, 11)
    )

    channels_rows = "\n".join(
        f"| Channel {idx} | {idx * 10000} | Week {idx} | Medium | Content type {idx} |"
        for idx in range(1, 4)
    )

    content_rows = "\n".join(
        f"| {idx} | Content piece {idx} | Channel {idx} | Purpose {idx} |"
        for idx in range(1, 7)
    )

    community_rows = "\n".join(
        f"| Mechanism {idx} | Week {idx} | Why statement {idx} |"
        for idx in range(1, 5)
    )

    partnership_rows = "\n".join(
        f"| Partner type {idx} | Target {idx} | One-line pitch {idx} | Quarter {idx} |"
        for idx in range(1, 4)
    )

    growth_rows = "\n".join(
        f"| Milestone {idx} | 2026-0{idx}-15 | Strategy path {idx} |"
        for idx in range(1, 5)
    )

    contrarian_rows = "\n".join(
        f"| Assumption {idx} | Contrarian challenge {idx} | {20 + idx}% | Hedge strategy {idx} |"
        for idx in range(1, 6)
    )

    appendix_extra = "\n".join(
        f"- Additional evidence point {idx}: quantified detail with decision rationale."
        for idx in range(1, 90)
    )

    return f"""---
artifact: execution_plan
phase: strategy
schema_version: "1.0"
generated: 2026-03-03T00:00:00Z
derived_from: .ideas/brainstorm-expansion.md
enables: .ideas/evaluation-results.md
---

# {project_name} - Strategic Execution Plan

**Date:** 2026-03-03T00:00:00Z
**Status:** Draft v1.0
**Objective:** Deliver a robust roadmap with explicit risk and execution controls.

## 1. Second-Order Thinking & Anticipation Layer

### 1.1 Second-Order Effects by Initiative

#### Initiative 1: Native strategy workflow
| Order | Effect | Implication |
| --- | --- | --- |
| First | Better clarity | Teams converge faster |
| Second | Better handoffs | Reduced context loss |
| Third | Better governance | Fewer launch surprises |

**Key insight:** Strong strategy artifacts improve downstream implementation quality.

#### Initiative 2: Quality gate integration
| Order | Effect | Implication |
| --- | --- | --- |
| First | Better scoring discipline | Better release confidence |
| Second | Better backlog focus | Less rework |
| Third | Better communication | Faster stakeholder alignment |

**Key insight:** Governance and velocity improve together when scoring is explicit.

#### Initiative 3: Operator-first docs
| Order | Effect | Implication |
| --- | --- | --- |
| First | Lower onboarding friction | Faster adoption |
| Second | Higher consistency | Fewer manual mistakes |
| Third | Better observability | Easier debugging in CI |

**Key insight:** Documentation quality is an operational multiplier.

### 1.2 Failure Modes by Phase

| Phase | Failure mode | Probability | Mitigation |
| --- | --- | --- | --- |
| Phase 1 | Scope instability | 25% | Freeze acceptance criteria before coding |
| Phase 2 | Integration delays | 20% | Stage-gate checkpoints and owners |
| Phase 3 | Quality regressions | 18% | Expand regression suite and smoke tests |
| Phase 4 | Launch mismatch | 15% | Pre-launch review and blocker extraction |

### 1.3 Competitive Responses

Competitors may copy command names quickly; differentiation should emphasize contract quality and workflow coherence.

### 1.4 Timing Risks

External release cycles and major ecosystem changes can shift launch windows; mitigation is phased delivery with rollback-ready increments.

### 1.5 Dependencies & Critical Path

Critical path: strategy artifacts -> execution plan -> strategic review -> integration closure report.

## 2. Polish & Improvements Before Public Exposure

### 2.1 Code Quality Audit Checklist

| Area | Status (PASS/PARTIAL/FAIL) | Action Needed | Priority |
| --- | --- | --- | --- |
| Tests | PASS | Keep adding edge-case coverage | High |
| Error handling | PARTIAL | Improve actionable diagnostics | High |
| Security | PASS | Keep path/symlink guards in place | High |
| CI/CD | PARTIAL | Extend smoke checks for new commands | Medium |
| Documentation | PARTIAL | Keep traceability map in sync | Medium |

### 2.2 Documentation Gaps

| Document | Exists (YES/NO) | Action |
| --- | --- | --- |
| README.md | YES | Add execution-plan mention in workflow |
| CONTRIBUTING.md | YES | Keep issue taxonomy examples fresh |
| CHANGELOG.md | YES | Keep release notes hydrated |
| Architecture docs | YES | Link strategy parity decisions |
| API/CLI docs | YES | Add command examples and validator notes |

### 2.3 README Optimization

README should surface command order, strategic value proposition, and quick examples for first-time users.

### 2.4 Demo/GIF/Video Needs

Add a short walkthrough showing strategy pre-phase flowing into Phase 0 and SDD.

### 2.5 Pre-Launch Evaluation Checkpoint

Before launch, run structured evaluation and advanced-evaluation checks; publish results in evaluation artifacts.

## 3. Expected Impacts Matrix

| Item | Reach | Effort (days) | Star Impact | Revenue | Moat Contribution |
| --- | --- | --- | --- | --- | --- |
{impacts}

## 4. Operationalized Roadmap

{roadmap_blocks}

## 4b. Pre-Mortem Analysis

| # | Cause of Death | Category | Probability | Prevention |
| --- | --- | --- | --- | --- |
{pre_mortem_rows}

## 4c. Moat Assessment

| Moat Type | Current | Buildable? | How | Timeline |
| --- | --- | --- | --- | --- |
{moat_rows}

## 5. Risk Register

| # | Risk | Prob. | Impact | Mitigation |
| --- | --- | --- | --- | --- |
{risk_rows}

## 6. Growth & Visibility Strategy

### 6.1 Launch Channels

| Channel | Audience size | Timing | Expected impact | Content type |
| --- | --- | --- | --- | --- |
{channels_rows}

### 6.2 Content Strategy

| Week | Content piece | Channel | Purpose |
| --- | --- | --- | --- |
{content_rows}

### 6.3 Community Building

| Mechanism | When | Why |
| --- | --- | --- |
{community_rows}

### 6.4 Partnership Opportunities

| Partner type | Targets | Pitch (one line) | Timing |
| --- | --- | --- | --- |
{partnership_rows}

### 6.5 HN Title A/B Testing

1. Technical narrative focused on delivery quality.
2. Problem-first framing focused on strategic coherence.
3. Outcome-first framing focused on measurable launch readiness.

### 6.6 Star Growth Model

| Milestone | Target date | Strategy |
| --- | --- | --- |
{growth_rows}

## 7. Contrarian Challenges

| Assumption | Contrarian View | Prob. Wrong | Hedge |
| --- | --- | --- | --- |
{contrarian_rows}

## Appendices

### A. Immediate Action Items (This Week)

1. Finalize command docs and examples.
2. Validate cross-shell behavior in CI.
3. Run smoke checks in clean workspace.
4. Review risk register owners and dates.
5. Prepare closure notes for integration issue.

### B. Key Files Reference

- `templates/commands/execution-plan.md`
- `scripts/bash/execution-plan.sh`
- `scripts/powershell/execution-plan.ps1`
- `scripts/bash/validate-execution-plan.sh`
- `scripts/powershell/validate-execution-plan.ps1`

### C. Quantitative Analysis

{appendix_extra}
"""


class TestExecutionPlanScaffold:
    def test_creates_execution_plan_artifact(self, tmp_path):
        result = run(EXECUTION_PLAN, str(tmp_path))
        assert result.returncode == 0, result.stderr
        assert (tmp_path / ".ideas" / "execution-plan.md").exists()

    def test_frontmatter_present(self, tmp_path):
        run(EXECUTION_PLAN, str(tmp_path))
        content = (tmp_path / ".ideas" / "execution-plan.md").read_text(encoding="utf-8")
        assert "artifact: execution_plan" in content
        assert "phase: strategy" in content

    def test_required_sections_scaffolded(self, tmp_path):
        run(EXECUTION_PLAN, str(tmp_path))
        content = (tmp_path / ".ideas" / "execution-plan.md").read_text(encoding="utf-8")
        assert "## 1. Second-Order Thinking & Anticipation Layer" in content
        assert "## 7. Contrarian Challenges" in content

    def test_idempotent_no_overwrite(self, tmp_path):
        run(EXECUTION_PLAN, str(tmp_path))
        result2 = run(EXECUTION_PLAN, str(tmp_path))
        assert result2.returncode != 0

    def test_force_flag_overwrites(self, tmp_path):
        run(EXECUTION_PLAN, str(tmp_path))
        result2 = run(EXECUTION_PLAN, "--force", str(tmp_path))
        assert result2.returncode == 0

    def test_help_flag(self, tmp_path):
        result = run(EXECUTION_PLAN, "--help", cwd=tmp_path)
        assert result.returncode == 0
        assert "Usage:" in result.stdout

    def test_default_dir_is_cwd(self, tmp_path):
        result = run(EXECUTION_PLAN, cwd=tmp_path)
        assert result.returncode == 0
        assert (tmp_path / ".ideas" / "execution-plan.md").exists()


class TestExecutionPlanValidator:
    def test_validator_fails_on_scaffold_with_todo(self, tmp_path):
        run(EXECUTION_PLAN, str(tmp_path))
        artifact = tmp_path / ".ideas" / "execution-plan.md"
        result = run(VALIDATE_EXECUTION_PLAN, str(artifact))
        assert result.returncode != 0

    def test_validator_passes_on_complete_document(self, tmp_path):
        ideas_dir = tmp_path / ".ideas"
        ideas_dir.mkdir(parents=True, exist_ok=True)
        artifact = ideas_dir / "execution-plan.md"
        artifact.write_text(_build_valid_execution_plan("Validation Demo"), encoding="utf-8")

        result = run(VALIDATE_EXECUTION_PLAN, str(artifact))
        assert result.returncode == 0, result.stderr

    def test_validator_fails_when_section_missing(self, tmp_path):
        ideas_dir = tmp_path / ".ideas"
        ideas_dir.mkdir(parents=True, exist_ok=True)
        artifact = ideas_dir / "execution-plan.md"
        content = _build_valid_execution_plan("Missing Section Demo").replace(
            "## 4b. Pre-Mortem Analysis", "## 4b. Pre-Mortem Analysis REMOVED"
        )
        artifact.write_text(content, encoding="utf-8")

        result = run(VALIDATE_EXECUTION_PLAN, str(artifact))
        assert result.returncode != 0

    def test_validator_rejects_malformed_risk_rows(self, tmp_path):
        ideas_dir = tmp_path / ".ideas"
        ideas_dir.mkdir(parents=True, exist_ok=True)
        artifact = ideas_dir / "execution-plan.md"
        content = _build_valid_execution_plan("Malformed Risk Table Demo").replace(
            "| 1 | Risk item 1 |", "|| 1 | Risk item 1 |"
        )
        artifact.write_text(content, encoding="utf-8")

        result = run(VALIDATE_EXECUTION_PLAN, str(artifact))
        assert result.returncode != 0


@skip_no_pwsh
class TestExecutionPlanPowerShell:
    def test_creates_execution_plan_artifact(self, tmp_path):
        result = run_ps1(EXECUTION_PLAN_PS1, str(tmp_path))
        assert result.returncode == 0, result.stderr
        assert (tmp_path / ".ideas" / "execution-plan.md").exists()

    def test_force_flag_overwrites(self, tmp_path):
        run_ps1(EXECUTION_PLAN_PS1, str(tmp_path))
        result = run_ps1(EXECUTION_PLAN_PS1, "-Force", str(tmp_path))
        assert result.returncode == 0

    def test_validator_fails_on_scaffold_with_todo(self, tmp_path):
        run_ps1(EXECUTION_PLAN_PS1, str(tmp_path))
        artifact = tmp_path / ".ideas" / "execution-plan.md"
        result = run_ps1(VALIDATE_EXECUTION_PLAN_PS1, str(artifact))
        assert result.returncode != 0

    def test_validator_passes_on_complete_document(self, tmp_path):
        ideas_dir = tmp_path / ".ideas"
        ideas_dir.mkdir(parents=True, exist_ok=True)
        artifact = ideas_dir / "execution-plan.md"
        artifact.write_text(_build_valid_execution_plan("PowerShell Validation Demo"), encoding="utf-8")

        result = run_ps1(VALIDATE_EXECUTION_PLAN_PS1, str(artifact))
        assert result.returncode == 0, result.stderr

    def test_validator_rejects_malformed_risk_rows(self, tmp_path):
        ideas_dir = tmp_path / ".ideas"
        ideas_dir.mkdir(parents=True, exist_ok=True)
        artifact = ideas_dir / "execution-plan.md"
        content = _build_valid_execution_plan("PowerShell Malformed Risk Table Demo").replace(
            "| 1 | Risk item 1 |", "|| 1 | Risk item 1 |"
        )
        artifact.write_text(content, encoding="utf-8")

        result = run_ps1(VALIDATE_EXECUTION_PLAN_PS1, str(artifact))
        assert result.returncode != 0
