"""Tests for strategic brainstorm scaffolding and validation scripts (issue #204)."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

SCRIPT_DIR = Path(__file__).parent.parent / "scripts" / "bash"
PS1_DIR = Path(__file__).parent.parent / "scripts" / "powershell"

BRAINSTORM = SCRIPT_DIR / "brainstorm.sh"
VALIDATE_BRAINSTORM = SCRIPT_DIR / "validate-brainstorm.sh"
BRAINSTORM_PS1 = PS1_DIR / "brainstorm.ps1"
VALIDATE_BRAINSTORM_PS1 = PS1_DIR / "validate-brainstorm.ps1"

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


def _build_valid_brainstorm(project_name: str = "Demo") -> str:
    divergent = "\n".join(
        f"{idx}. Idea {idx} for strategic expansion with measurable impact and clear rationale."
        for idx in range(1, 21)
    )

    tier_entries = "\n\n".join(
        f"#### S{idx}: Strategic initiative {idx}\n"
        f"What: Initiative {idx} delivers differentiated value in the next 12 months.\n"
        f"Why huge: Captures a strong underserved segment with clear urgency.\n"
        f"Path: Step 1 define scope; Step 2 prototype; Step 3 validate; Step 4 roll out.\n"
        f"Comparable: Comparable project {idx} showed similar adoption curve.\n"
        f"Risk: Execution complexity is medium and mitigated by staged rollout.\n"
        f"Effort: Medium."
        for idx in range(1, 4)
    )

    scamper_sections = []
    for lens in [
        "S — Substitute",
        "C — Combine",
        "A — Adapt",
        "M — Modify / Magnify",
        "P — Put to Other Uses",
        "E — Eliminate",
        "R — Reverse / Rearrange",
    ]:
        bullets = "\n".join(
            f"- {lens} option {i}: concrete strategic move tied to customer value." for i in range(1, 5)
        )
        scamper_sections.append(f"### {lens}\n{bullets}")

    risk_rows = "\n".join(
        f"| Risk {idx} | {'High' if idx % 2 else 'Medium'} | Medium | Mitigation plan {idx} |"
        for idx in range(1, 6)
    )

    actions = "\n".join(
        f"{idx}. Execute high-leverage action {idx} with clear owner and due date."
        for idx in range(1, 6)
    )

    extra_depth = "\n".join(
        f"- Additional depth insight {idx}: structured evidence and trade-off framing."
        for idx in range(1, 45)
    )

    return f"""---
artifact: brainstorm_expansion
phase: strategy
schema_version: "1.0"
generated: 2026-03-02T00:00:00Z
derived_from: null
enables: .spec-kit/ideas_backlog.md
---

# {project_name} — Strategic Brainstorm

**Date:** 2026-03-02T00:00:00Z
**Objective:** Build a strategy artifact that improves ideation quality and execution focus.

---

## 1. What Is the REAL Asset?

The real asset is the decision framework + reusable artifact chain that compounds quality over time.

## 2. SCAMPER Analysis

{chr(10).join(scamper_sections)}

## 3. Divergent Ideation — 20 Wild Ideas

{divergent}

## 4. Convergent Analysis — Tier Ranking

### Tier S — Transformative (100k+ potential)

{tier_entries}

### Tier A — High Impact (10k-50k potential)

#### A1: Productized orchestration lane
What: Productize the orchestration lane with strict acceptance gates.
Why huge: Reduces operational friction and increases delivery consistency.
Path: Scope, pilot, instrument, expand.
Comparable: Similar workflow productization in mature engineering orgs.
Risk: Medium; mitigated by phased rollout.
Effort: Medium.

### Tier B — Strong (1k-10k potential)

- Documented command discoverability improvements.
- Better CI hints for operators.
- Faster onboarding with guided examples.

## 5. Blue Ocean Strategy

### Current Market (Red Ocean)

| Existing Solution | Weakness |
| --- | --- |
| Generic prompting tools | No deterministic artifact contracts |
| Ad-hoc templates | Poor traceability and no quality gates |
| Fragmented workflows | Weak continuity across stages |

### Blue Ocean Opportunity

Unique positioning comes from strategy + Phase 0 + SDD continuity in one governed workflow.

## 6. TAM/SAM/SOM

| Segment | TAM | SAM | SOM |
| --- | --- | --- | --- |
| AI-first teams | 1,000,000 | 250,000 | 25,000 |
| OSS maintainers | 500,000 | 120,000 | 12,000 |
| Product teams | 800,000 | 200,000 | 20,000 |

Key insight: start with teams already using structured issue/PR workflows.

## 7. Jobs-to-be-Done

- When I coordinate an AI-heavy roadmap, I want structured strategic options so I can reduce bad bets.
- When I review feature proposals, I want explicit risks and assumptions so I can decide faster.
- When I hand off to implementation, I want traceable artifacts so I can preserve intent.

## 8. Flywheel

More strategic clarity -> better idea quality -> higher implementation success -> more trust -> more strategic clarity.

Push point: artifact quality at the strategy boundary.
Friction points: weak evidence, missing ownership, and low validation discipline.

## 9. One-Line Pitches

1. For developers: turn rough ideas into actionable, testable strategy artifacts.
2. For enterprises: de-risk AI roadmap decisions with repeatable strategic rigor.
3. For AI companies: convert model capability exploration into productizable initiatives.
4. For investors: reveal strategic optionality with explicit risk and execution pathways.
5. For CLI/tool authors: embed strategic depth into existing command-driven workflows.

## 10. Honest Weaknesses & Risks

| Weakness | Severity | Probability | Mitigation |
| --- | --- | --- | --- |
{risk_rows}

## 11. Monday Morning Actions

{actions}

{extra_depth}
"""


class TestBrainstormScaffold:
    def test_creates_brainstorm_artifact(self, tmp_path):
        result = run(BRAINSTORM, str(tmp_path))
        assert result.returncode == 0, result.stderr
        assert (tmp_path / ".ideas" / "brainstorm-expansion.md").exists()

    def test_frontmatter_present(self, tmp_path):
        run(BRAINSTORM, str(tmp_path))
        content = (tmp_path / ".ideas" / "brainstorm-expansion.md").read_text(encoding="utf-8")
        assert "artifact: brainstorm_expansion" in content
        assert "phase: strategy" in content

    def test_required_sections_scaffolded(self, tmp_path):
        run(BRAINSTORM, str(tmp_path))
        content = (tmp_path / ".ideas" / "brainstorm-expansion.md").read_text(encoding="utf-8")
        assert "## 1. What Is the REAL Asset?" in content
        assert "## 11. Monday Morning Actions" in content

    def test_idempotent_no_overwrite(self, tmp_path):
        run(BRAINSTORM, str(tmp_path))
        result2 = run(BRAINSTORM, str(tmp_path))
        assert result2.returncode != 0

    def test_force_flag_overwrites(self, tmp_path):
        run(BRAINSTORM, str(tmp_path))
        result2 = run(BRAINSTORM, "--force", str(tmp_path))
        assert result2.returncode == 0

    def test_help_flag(self, tmp_path):
        result = run(BRAINSTORM, "--help", cwd=tmp_path)
        assert result.returncode == 0
        assert "Usage:" in result.stdout

    def test_default_dir_is_cwd(self, tmp_path):
        result = run(BRAINSTORM, cwd=tmp_path)
        assert result.returncode == 0
        assert (tmp_path / ".ideas" / "brainstorm-expansion.md").exists()


class TestBrainstormValidator:
    def test_validator_fails_on_scaffold_with_todo(self, tmp_path):
        run(BRAINSTORM, str(tmp_path))
        artifact = tmp_path / ".ideas" / "brainstorm-expansion.md"
        result = run(VALIDATE_BRAINSTORM, str(artifact))
        assert result.returncode != 0

    def test_validator_passes_on_complete_document(self, tmp_path):
        ideas_dir = tmp_path / ".ideas"
        ideas_dir.mkdir(parents=True, exist_ok=True)
        artifact = ideas_dir / "brainstorm-expansion.md"
        artifact.write_text(_build_valid_brainstorm("Validation Demo"), encoding="utf-8")

        result = run(VALIDATE_BRAINSTORM, str(artifact))
        assert result.returncode == 0, result.stderr

    def test_validator_fails_when_section_missing(self, tmp_path):
        ideas_dir = tmp_path / ".ideas"
        ideas_dir.mkdir(parents=True, exist_ok=True)
        artifact = ideas_dir / "brainstorm-expansion.md"
        content = _build_valid_brainstorm("Missing Section Demo").replace(
            "## 8. Flywheel", "## 8. Flywheel REMOVED"
        )
        artifact.write_text(content, encoding="utf-8")

        result = run(VALIDATE_BRAINSTORM, str(artifact))
        assert result.returncode != 0


@skip_no_pwsh
class TestBrainstormPowerShell:
    def test_creates_brainstorm_artifact(self, tmp_path):
        result = run_ps1(BRAINSTORM_PS1, str(tmp_path))
        assert result.returncode == 0, result.stderr
        assert (tmp_path / ".ideas" / "brainstorm-expansion.md").exists()

    def test_force_flag_overwrites(self, tmp_path):
        run_ps1(BRAINSTORM_PS1, str(tmp_path))
        result = run_ps1(BRAINSTORM_PS1, "-Force", str(tmp_path))
        assert result.returncode == 0

    def test_validator_fails_on_scaffold_with_todo(self, tmp_path):
        run_ps1(BRAINSTORM_PS1, str(tmp_path))
        artifact = tmp_path / ".ideas" / "brainstorm-expansion.md"
        result = run_ps1(VALIDATE_BRAINSTORM_PS1, str(artifact))
        assert result.returncode != 0

    def test_validator_passes_on_complete_document(self, tmp_path):
        ideas_dir = tmp_path / ".ideas"
        ideas_dir.mkdir(parents=True, exist_ok=True)
        artifact = ideas_dir / "brainstorm-expansion.md"
        artifact.write_text(_build_valid_brainstorm("PowerShell Validation Demo"), encoding="utf-8")

        result = run_ps1(VALIDATE_BRAINSTORM_PS1, str(artifact))
        assert result.returncode == 0, result.stderr
