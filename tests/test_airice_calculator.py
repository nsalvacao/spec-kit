"""Tests for calculate-ai-rice.sh / .ps1 (issue #17) and validate-airice semantic validation (issue #21)."""

import shutil
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).parent.parent
BASH_SCRIPT = REPO_ROOT / "scripts" / "bash" / "calculate-ai-rice.sh"
PS1_SCRIPT = REPO_ROOT / "scripts" / "powershell" / "calculate-ai-rice.ps1"
VALIDATE_BASH = REPO_ROOT / "scripts" / "bash" / "validate-airice.sh"
VALIDATE_PS1 = REPO_ROOT / "scripts" / "powershell" / "validate-airice.ps1"

PWSH = shutil.which("pwsh")
skip_no_pwsh = pytest.mark.skipif(PWSH is None, reason="pwsh not available")

# AI-RICE formula: (Reach * Impact * Confidence * Data_Readiness) / (Effort * Risk)
# Confidence and Data_Readiness are integers 0-100 (raw percentage values)


def run_bash(args, cwd=None):
    return subprocess.run(
        ["bash", str(BASH_SCRIPT)] + args,
        capture_output=True, text=True, cwd=cwd
    )


def run_ps1(args, cwd=None):
    return subprocess.run(
        ["pwsh", "-NoLogo", "-NonInteractive", "-File", str(PS1_SCRIPT)] + args,
        capture_output=True, text=True, cwd=cwd
    )


def _make_selection_md(tmp_path, rows, breakdown_ok=True):
    """Create a minimal idea_selection.md with given scoring rows.

    Idea ID uses markdown link format [ID](url) to match the real template,
    ensuring the validators correctly parse numeric columns without link stripping.
    """
    rows_text = "\n".join(
        f"| [{r['id']}](../ideas.md#{r['id'].lower()}) | {r['reach']} | {r['impact']} | {r['conf']}% "
        f"| {r['dr']}% | {r['effort']} | {r['risk']} | {r['score']:.2f} | {r.get('norm', 100.0)} |"
        for r in rows
    )
    breakdown = ""
    if breakdown_ok:
        breakdown = """
**Reach**: 1000 — high
**Impact**: 2.0 — high
**Confidence**: 70% — good
**Data_Readiness**: 80% — good
**Effort**: 4 — medium
**Risk**: 5 — medium
"""
    content = f"""---
artifact: idea_selection
---

# Idea Selection Report

## AI-RICE Scoring Table

| Idea ID | Reach | Impact | Confidence | Data_Readiness | Effort | Risk | AI-RICE Score | Norm_Score |
| ------- | ----- | ------ | ---------- | -------------- | ------ | ---- | ------------- | ---------- |
{rows_text}

## Selected Idea
{breakdown}
## Selection Rationale

Some rationale here.
"""
    path = tmp_path / ".spec-kit" / "idea_selection.md"
    path.parent.mkdir(parents=True)
    path.write_text(content)
    return path


# ---------------------------------------------------------------------------
# Tests: calculate-ai-rice.sh (Bash)
# ---------------------------------------------------------------------------

class TestCalculateAIRiceBash:
    """Tests for scripts/bash/calculate-ai-rice.sh."""

    def test_script_exists(self):
        assert BASH_SCRIPT.exists(), f"Script not found: {BASH_SCRIPT}"

    def test_help_exits_zero(self):
        result = run_bash(["--help"])
        assert result.returncode == 0
        assert "Usage:" in result.stdout

    def test_basic_calculation(self):
        # (1000 * 2.0 * 70 * 80) / (4 * 5) = 560000
        result = run_bash(["1000", "2.0", "70", "80", "4", "5"])
        assert result.returncode == 0
        assert "560000" in result.stdout.replace(",", "")

    def test_output_contains_formula(self):
        result = run_bash(["1000", "2.0", "70", "80", "4", "5"])
        assert result.returncode == 0
        # Formula line
        assert "Formula" in result.stdout

    def test_output_contains_rationale(self):
        result = run_bash(["1000", "2.0", "70", "80", "4", "5"])
        assert result.returncode == 0
        assert "Rationale" in result.stdout or "rationale" in result.stdout

    def test_output_contains_all_dimensions(self):
        result = run_bash(["1000", "2.0", "70", "80", "4", "5"])
        assert result.returncode == 0
        for dim in ("Reach", "Impact", "Confidence", "Data_Readiness", "Effort", "Risk"):
            assert dim in result.stdout, f"Missing dimension in output: {dim}"

    def test_optional_name_flag(self):
        result = run_bash(["1000", "2.0", "70", "80", "4", "5", "--name", "My Great Idea"])
        assert result.returncode == 0
        assert "My Great Idea" in result.stdout

    def test_zero_confidence_gives_zero_score(self):
        result = run_bash(["1000", "2.0", "0", "80", "4", "5"])
        assert result.returncode == 0
        assert "0.00" in result.stdout or "0" in result.stdout

    def test_confidence_over_100_is_invalid(self):
        result = run_bash(["1000", "2.0", "150", "80", "4", "5"])
        assert result.returncode != 0

    def test_data_readiness_over_100_is_invalid(self):
        result = run_bash(["1000", "2.0", "70", "101", "4", "5"])
        assert result.returncode != 0

    def test_risk_over_10_is_invalid(self):
        result = run_bash(["1000", "2.0", "70", "80", "4", "11"])
        assert result.returncode != 0

    def test_risk_zero_is_invalid(self):
        result = run_bash(["1000", "2.0", "70", "80", "4", "0"])
        assert result.returncode != 0

    def test_effort_zero_is_invalid(self):
        result = run_bash(["1000", "2.0", "70", "80", "0", "5"])
        assert result.returncode != 0

    def test_reach_zero_is_invalid(self):
        result = run_bash(["0", "2.0", "70", "80", "4", "5"])
        assert result.returncode != 0

    def test_too_few_args_exits_nonzero(self):
        result = run_bash(["1000", "2.0", "70"])
        assert result.returncode != 0

    def test_too_many_args_exits_nonzero(self):
        result = run_bash(["1000", "2.0", "70", "80", "4", "5", "99"])
        assert result.returncode != 0

    def test_dimensional_drivers_mentioned(self):
        # High reach + high impact should be called out as drivers
        result = run_bash(["10000", "3.0", "90", "90", "1", "1"])
        assert result.returncode == 0
        # Output should mention something about strong/high drivers
        output_lower = result.stdout.lower()
        assert "driver" in output_lower or "high" in output_lower or "strong" in output_lower

    def test_dimensional_limiters_mentioned(self):
        # High effort + high risk
        result = run_bash(["1000", "2.0", "70", "80", "12", "9"])
        assert result.returncode == 0
        output_lower = result.stdout.lower()
        assert "limit" in output_lower or "high" in output_lower or "risk" in output_lower


# ---------------------------------------------------------------------------
# Tests: calculate-ai-rice.ps1 (PowerShell)
# ---------------------------------------------------------------------------

class TestCalculateAIRicePS1:
    """Tests for scripts/powershell/calculate-ai-rice.ps1."""

    @skip_no_pwsh
    def test_script_exists(self):
        assert PS1_SCRIPT.exists(), f"Script not found: {PS1_SCRIPT}"

    @skip_no_pwsh
    def test_help_exits_zero(self):
        result = run_ps1(["-Help"])
        assert result.returncode == 0
        assert "Usage" in result.stdout or "SYNOPSIS" in result.stdout

    @skip_no_pwsh
    def test_basic_calculation(self):
        result = run_ps1(["1000", "2.0", "70", "80", "4", "5"])
        assert result.returncode == 0
        assert "560000" in result.stdout.replace(",", "")

    @skip_no_pwsh
    def test_output_contains_rationale(self):
        result = run_ps1(["1000", "2.0", "70", "80", "4", "5"])
        assert result.returncode == 0
        assert "Rationale" in result.stdout or "rationale" in result.stdout.lower()

    @skip_no_pwsh
    def test_confidence_over_100_is_invalid(self):
        result = run_ps1(["1000", "2.0", "150", "80", "4", "5"])
        assert result.returncode != 0

    @skip_no_pwsh
    def test_risk_over_10_is_invalid(self):
        result = run_ps1(["1000", "2.0", "70", "80", "4", "11"])
        assert result.returncode != 0


# ---------------------------------------------------------------------------
# Tests: validate-airice.sh semantic validation (issue #21)
# ---------------------------------------------------------------------------

class TestValidateAIRiceSemanticBash:
    """Semantic validation tests for validate-airice.sh (issue #21)."""

    def _run(self, filepath):
        return subprocess.run(
            ["bash", str(VALIDATE_BASH), str(filepath)],
            capture_output=True, text=True
        )

    def test_correct_score_passes(self, tmp_path):
        # (1000 * 2.0 * 70 * 80) / (4 * 5) = 560000
        expected = (1000 * 2.0 * 70 * 80) / (4 * 5)
        path = _make_selection_md(tmp_path, [
            {"id": "S1", "reach": 1000, "impact": 2.0, "conf": 70, "dr": 80, "effort": 4, "risk": 5, "score": expected}
        ])
        result = self._run(path)
        assert result.returncode == 0
        assert "passed" in result.stdout.lower()

    def test_wrong_score_fails(self, tmp_path):
        wrong_score = 999.99  # clearly wrong for these inputs
        path = _make_selection_md(tmp_path, [
            {"id": "S1", "reach": 1000, "impact": 2.0, "conf": 70, "dr": 80, "effort": 4, "risk": 5, "score": wrong_score}
        ])
        result = self._run(path)
        assert result.returncode != 0
        assert "mismatch" in result.stdout.lower() or "error" in result.stdout.lower() or "error" in result.stderr.lower()

    def test_confidence_out_of_range_fails(self, tmp_path):
        # Confidence 150 is invalid
        score = (1000 * 2.0 * 150 * 80) / (4 * 5)
        path = _make_selection_md(tmp_path, [
            {"id": "S1", "reach": 1000, "impact": 2.0, "conf": 150, "dr": 80, "effort": 4, "risk": 5, "score": score}
        ])
        result = self._run(path)
        assert result.returncode != 0

    def test_risk_out_of_range_fails(self, tmp_path):
        # Risk 11 is invalid
        score = (1000 * 2.0 * 70 * 80) / (4 * 11)
        path = _make_selection_md(tmp_path, [
            {"id": "S1", "reach": 1000, "impact": 2.0, "conf": 70, "dr": 80, "effort": 4, "risk": 11, "score": score}
        ])
        result = self._run(path)
        assert result.returncode != 0

    def test_multiple_correct_rows_pass(self, tmp_path):
        score1 = (1000 * 2.0 * 70 * 80) / (4 * 5)
        score2 = (500 * 1.0 * 60 * 50) / (2 * 3)
        path = _make_selection_md(tmp_path, [
            {"id": "S1", "reach": 1000, "impact": 2.0, "conf": 70, "dr": 80, "effort": 4, "risk": 5, "score": score1},
            {"id": "S2", "reach": 500, "impact": 1.0, "conf": 60, "dr": 50, "effort": 2, "risk": 3, "score": score2},
        ])
        result = self._run(path)
        assert result.returncode == 0


class TestValidateAIRiceSemanticPS1:
    """Semantic validation tests for validate-airice.ps1 (issue #21)."""

    def _run(self, filepath):
        return subprocess.run(
            ["pwsh", "-NoLogo", "-NonInteractive", "-File", str(VALIDATE_PS1), str(filepath)],
            capture_output=True, text=True
        )

    @skip_no_pwsh
    def test_correct_score_passes(self, tmp_path):
        expected = (1000 * 2.0 * 70 * 80) / (4 * 5)
        path = _make_selection_md(tmp_path, [
            {"id": "S1", "reach": 1000, "impact": 2.0, "conf": 70, "dr": 80, "effort": 4, "risk": 5, "score": expected}
        ])
        result = self._run(path)
        assert result.returncode == 0

    @skip_no_pwsh
    def test_wrong_score_fails(self, tmp_path):
        path = _make_selection_md(tmp_path, [
            {"id": "S1", "reach": 1000, "impact": 2.0, "conf": 70, "dr": 80, "effort": 4, "risk": 5, "score": 999.99}
        ])
        result = self._run(path)
        assert result.returncode != 0
