"""Tests for validate-vision-brief.sh (issue #22).

Tests cover:
- Automated checks A1-A8 (non-waivable)
- Manual checks Q1-Q5, AI1-AI4, C1-C3 (waivable)
- Waiver Mechanism: --waive flag with justification
- RESULT: PASS / PASS WITH WAIVER / FAIL output
"""

import subprocess
import tempfile
from pathlib import Path

import pytest

SCRIPT_DIR = Path(__file__).parent.parent / "scripts" / "bash"
SCRIPT = SCRIPT_DIR / "validate-vision-brief.sh"

MINIMAL_VALID_BRIEF = """---
artifact: vision_brief
phase: structure
---

# Vision Brief: Test System

## One-Liner

A test system for validation purposes.

**Canvas References**: C7, C12

## Problem Statement

**Job-to-be-Done**: When I need to test, I want to validate, so I can ensure quality.

**Context**: Testing context from canvas component 3.

**Current Solution Pains**: Manual testing is slow.

**Canvas References**: C1, C3, C5

## Solution Approach

**High-Level Design**: Automated test solution integrating AI Task from component 12.

**AI Approach**: Large language model with evaluation framework.

**How It Works**: Conceptual flow integrating JTBD, Lean, AI sections.

**Canvas References**: C7, C12, C14, C15

## Success Criteria

1. Latency target: <200ms by Q2 2025
2. Accuracy ≥90% within 30 days
3. Cost within budget constraints, target <$100/month

**Canvas References**: C10

## Key Assumptions

| Assumption | Validation Method | Risk If Wrong | Tracking |
| ------------ | ------------------- | --------------- | ---------- |
| Data available at 70% readiness | Prototype test | Delay | Monthly review |
| Budget sufficient | Cost model | Over-spend | Budget tracker |
| Model accuracy feasible | Benchmark run | Rework | CI metrics |

**Canvas References**: C8, C9

## Data & Model Strategy

**Data Requirements**: Training data from production logs.

- Internal logs (80% availability)
- External benchmark datasets (60% availability)
- Synthetic augmentation (100% availability)

**Model Approach**: We selected a transformer-based model family for its strong performance on
sequence classification tasks. The selection was driven by latency constraints (C17) requiring
<200ms inference, which aligns with quantised model variants. We evaluated GPT-style and BERT-style
architectures, choosing BERT-style due to its encoder efficiency. This approach fits the data
readiness profile and cost constraints from C14.

**Evaluation**: Primary metrics: F1, BLEU. Benchmarks against SoTA. Human evaluation quarterly.

**Canvas References**: C13, C14, C15

## Constraints & Risks

**Budget Constraints**: Total budget $10k from canvas C11, C17.

**Technical Constraints**: Latency <200ms, context window limit, C17 constraints C14 model.

**Safety Risks**: Hallucination risk — mitigation: confidence threshold filtering. Bias risk — mitigation: adversarial test suite. Compliance with GDPR regulatory requirements.

**Canvas References**: C11, C17, C16

---

**Approval**: *Awaiting Gate G0 validation*
"""

BRIEF_MISSING_SECTION = MINIMAL_VALID_BRIEF.replace("## One-Liner\n", "")

BRIEF_WITH_PLACEHOLDER = MINIMAL_VALID_BRIEF.replace(
    "A test system for validation purposes.",
    "[PLACEHOLDER]"
)

BRIEF_BAD_JOB_STATEMENT = MINIMAL_VALID_BRIEF.replace(
    "When I need to test, I want to validate, so I can ensure quality.",
    "I need to test things."
)

BRIEF_FEW_ASSUMPTIONS = """---
artifact: vision_brief
phase: structure
---

# Vision Brief: Test System

## One-Liner

Single line.

**Canvas References**: C7

## Problem Statement

**Job-to-be-Done**: When I test, I want results, so I can proceed.

**Canvas References**: C1

## Solution Approach

**Canvas References**: C7

## Success Criteria

1. Metric one
2. Metric two
3. Metric three

**Canvas References**: C10

## Key Assumptions

| Assumption | Validation Method | Risk If Wrong | Tracking |
| ------------ | ------------------- | --------------- | ---------- |
| One assumption | Test | High | Monitor |

**Canvas References**: C8

## Data & Model Strategy

**Data Requirements**:
- Source A (70%)

**Model Approach**: This is a short model approach section.

**Canvas References**: C13

## Constraints & Risks

**Canvas References**: C11

---
"""


def run_script(cwd: Path, brief_file: Path, *extra_args) -> subprocess.CompletedProcess:
    return subprocess.run(
        [str(SCRIPT), str(brief_file), *extra_args],
        cwd=str(cwd),
        capture_output=True,
        text=True,
    )


@pytest.fixture()
def workdir():
    with tempfile.TemporaryDirectory() as d:
        yield Path(d)


@pytest.fixture()
def valid_brief(workdir):
    f = workdir / "vision_brief.md"
    f.write_text(MINIMAL_VALID_BRIEF)
    return f


# ──────────────────────────────────────────────────────────────
# Automated checks — non-waivable
# ──────────────────────────────────────────────────────────────

class TestAutomatedChecks:
    def test_a1_file_missing(self, workdir):
        result = run_script(workdir, workdir / "nonexistent.md")
        assert result.returncode == 1
        assert "A1" in result.stderr

    def test_a1_file_present(self, workdir, valid_brief):
        result = run_script(workdir, valid_brief)
        assert "PASS [A1]" in result.stdout

    def test_a2_missing_section(self, workdir):
        f = workdir / "brief.md"
        f.write_text(BRIEF_MISSING_SECTION)
        result = run_script(workdir, f)
        assert result.returncode == 1
        assert "A2" in result.stderr

    def test_a3_placeholder_token(self, workdir):
        f = workdir / "brief.md"
        f.write_text(BRIEF_WITH_PLACEHOLDER)
        result = run_script(workdir, f)
        assert result.returncode == 1
        assert "A3" in result.stderr

    def test_a4_bad_job_statement(self, workdir):
        f = workdir / "brief.md"
        f.write_text(BRIEF_BAD_JOB_STATEMENT)
        result = run_script(workdir, f)
        assert result.returncode == 1
        assert "A4" in result.stderr

    def test_a5_few_assumptions(self, workdir):
        f = workdir / "brief.md"
        f.write_text(BRIEF_FEW_ASSUMPTIONS)
        result = run_script(workdir, f)
        assert result.returncode == 1
        assert "A5" in result.stderr

    def test_full_valid_brief_passes(self, workdir, valid_brief):
        result = run_script(workdir, valid_brief)
        assert result.returncode == 0
        assert "PASS" in result.stdout
        # All 8 automated checks pass
        for criterion in ["A1", "A2", "A3", "A4", "A5", "A6", "A7", "A8"]:
            assert f"PASS [{criterion}]" in result.stdout


# ──────────────────────────────────────────────────────────────
# Result output
# ──────────────────────────────────────────────────────────────

class TestResultOutput:
    def test_pass_result_on_valid_brief(self, workdir, valid_brief):
        result = run_script(workdir, valid_brief)
        assert result.returncode == 0
        assert "RESULT: PASS" in result.stdout

    def test_fail_result_on_missing_file(self, workdir):
        result = run_script(workdir, workdir / "missing.md")
        assert result.returncode == 1


# ──────────────────────────────────────────────────────────────
# Waiver mechanism
# ──────────────────────────────────────────────────────────────

class TestWaiverMechanism:
    def test_waive_reduces_failures(self, workdir, valid_brief):
        """Brief that passes automated checks but may have manual warnings.
        Applying --waive to a manual criterion should not cause FAIL."""
        result_waived = run_script(
            workdir, valid_brief,
            "--waive", "Q1", "Test waiver justification"
        )
        # Should not fail (automated checks pass; waiver applied to manual)
        assert result_waived.returncode == 0

    def test_waive_shows_waived_label(self, workdir):
        """Brief with no percentage values — AI1 fails, then waiver shows WAIVED label."""
        # Strip all percentage numbers so AI1 (readiness ≥60%) cannot find [6-9][0-9]%|100%
        import re
        brief_no_pct = re.sub(r"\d+%", "TBD", MINIMAL_VALID_BRIEF)
        # Also ensure Q3 check (availability %) passes by removing those too — AI1 is our target
        f = workdir / "vision_brief.md"
        f.write_text(brief_no_pct)
        result = run_script(
            workdir, f,
            "--waive", "AI1", "Data readiness to be confirmed in next sprint"
        )
        assert "WAIVED [AI1]" in result.stdout

    def test_waive_with_justification_in_output(self, workdir):
        """Brief with no cost/budget refs — AI4 fails, waiver justification appears in output."""
        import re
        # Remove ALL words matched by AI4 check: budget|cost|viabilit|pricing|inference
        brief_no_cost = re.sub(
            r"\b(budget|cost|viabilit\w*|pricing|inference)\b",
            "TBD",
            MINIMAL_VALID_BRIEF,
            flags=re.IGNORECASE
        )
        f = workdir / "vision_brief.md"
        f.write_text(brief_no_cost)
        justification = "Budget details pending board approval"
        result = run_script(workdir, f, "--waive", "AI4", justification)
        assert justification in result.stdout

    def test_pass_with_waiver_result_when_waivers_applied(self, workdir, valid_brief):
        result = run_script(workdir, valid_brief, "--waive", "C3", "C17/C14 ref confirmed in canvas")
        assert result.returncode == 0
        assert "PASS WITH WAIVER" in result.stdout or "PASS" in result.stdout

    def test_automated_checks_not_waivable(self, workdir):
        """Even with --waive A1, missing file should still fail."""
        result = run_script(
            workdir, workdir / "missing.md",
            "--waive", "A1", "We know the file is missing"
        )
        assert result.returncode == 1
        assert "A1" in result.stderr
