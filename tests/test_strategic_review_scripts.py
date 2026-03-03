"""Tests for strategic-review scaffolding and validation scripts (issue #206)."""

from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import subprocess

import pytest

ROOT_DIR = Path(__file__).parent.parent
SCRIPT_DIR = ROOT_DIR / "scripts" / "bash"
PS1_DIR = ROOT_DIR / "scripts" / "powershell"
SHARED_SCRIPTS_DIR = ROOT_DIR / "scripts"

STRATEGIC_REVIEW = SCRIPT_DIR / "strategic-review.sh"
VALIDATE_STRATEGIC_REVIEW = SCRIPT_DIR / "validate-strategic-review.sh"
STRATEGIC_REVIEW_PS1 = PS1_DIR / "strategic-review.ps1"
VALIDATE_STRATEGIC_REVIEW_PS1 = PS1_DIR / "validate-strategic-review.ps1"
STRATEGIC_REVIEW_RUNTIME = SHARED_SCRIPTS_DIR / "strategic-review-runtime.py"

PWSH = shutil.which("pwsh")
skip_no_pwsh = pytest.mark.skipif(PWSH is None, reason="pwsh not available")
SUBPROCESS_TIMEOUT_SECONDS = int(os.getenv("SPECIFY_TEST_SUBPROCESS_TIMEOUT_SECONDS", "30"))


def run(script: Path, *args, cwd=None) -> subprocess.CompletedProcess:
    if not script.exists():
        raise FileNotFoundError(f"Script not found: {script}")
    return subprocess.run(
        [str(script), *args],
        capture_output=True,
        text=True,
        cwd=cwd,
        timeout=SUBPROCESS_TIMEOUT_SECONDS,
    )


def run_ps1(script: Path, *args, cwd=None) -> subprocess.CompletedProcess:
    if not script.exists():
        raise FileNotFoundError(f"Script not found: {script}")
    return subprocess.run(
        [PWSH, "-NonInteractive", "-File", str(script), *args],
        capture_output=True,
        text=True,
        cwd=cwd,
        timeout=SUBPROCESS_TIMEOUT_SECONDS,
    )


def _weighted_total(scores: dict[str, float], weights: dict[str, float]) -> float:
    return sum(scores[key] * weights[key] for key in scores)


def _build_valid_strategic_review(
    *,
    project_name: str = "Demo",
    scores: dict[str, float] | None = None,
    blockers: list[str] | None = None,
    reported_band: str = "GREEN",
    report_date: str = "2026-03-03T00:00:00Z",
) -> str:
    weights = {
        "output_quality": 0.25,
        "readme_docs_quality": 0.20,
        "developer_experience": 0.20,
        "security_trust": 0.15,
        "competitive_positioning": 0.10,
        "test_coverage": 0.10,
    }
    default_scores = {
        "output_quality": 4.4,
        "readme_docs_quality": 4.2,
        "developer_experience": 4.3,
        "security_trust": 4.5,
        "competitive_positioning": 4.0,
        "test_coverage": 4.1,
    }
    merged_scores = {**default_scores, **(scores or {})}
    weighted_rows = []
    label_map = {
        "output_quality": "Output quality",
        "readme_docs_quality": "README/docs quality",
        "developer_experience": "Developer experience",
        "security_trust": "Security/trust",
        "competitive_positioning": "Competitive positioning",
        "test_coverage": "Test coverage",
    }

    for key, label in label_map.items():
        score = merged_scores[key]
        weight = weights[key]
        weighted = score * weight
        weighted_rows.append(f"| {label} | {score:.2f} | {weight:.2f} | {weighted:.2f} |")

    total = _weighted_total(merged_scores, weights)
    blockers = blockers or []
    blockers_text = "\n".join(f"{idx}. {item}" for idx, item in enumerate(blockers, start=1))
    if not blockers_text:
        blockers_text = "None."

    appendix_depth = "\n".join(
        f"- Evidence item {idx}: command output, file reference, and rationale."
        for idx in range(1, 75)
    )

    return f"""---
artifact: evaluation_results
phase: strategy
schema_version: "1.0"
generated: {report_date}
derived_from:
  - .ideas/brainstorm-expansion.md
  - .ideas/execution-plan.md
enables: .ideas/launch-blockers.md
---

# {project_name} -- Strategic Review (Pre-Launch Evaluation)

**Date:** {report_date}
**Overall Score:** {total:.2f}
**Band:** {reported_band}
**Recommendation:** {'Launch confidently' if reported_band == 'GREEN' else 'Fix blockers before launch'}

---

## 1. Output Quality Evaluation

Core generated outputs are complete and evidence-backed. Quality checks surfaced only bounded improvements.

## 2. Cross-Output Consistency

All outputs present aligned terminology, stable formatting, and no contradictory recommendations.

## 3. README Conversion Audit

README has clear value proposition, quick start, and proof points. Remaining improvements are polish-level.

## 4. Developer Experience Audit

Install and first-use flows were executed in clean workspace conditions and validated.

## 5. Security & Trust Audit

No hardcoded secrets detected, no unsafe subprocess patterns found, and attribution is coherent.

## 6. Competitive Positioning

Positioning remains differentiated in target segment, with realistic timing and channel assumptions.

## 7. Launch Readiness Scorecard

| Category | Score (1-5) | Weight | Weighted |
| --- | --- | --- | --- |
{chr(10).join(weighted_rows)}
| **TOTAL** | {total:.2f} | 1.00 | {total:.2f} |

## 8. Action Items

### Blockers (MUST fix)
{blockers_text}

### Improvements (SHOULD fix)
1. Refine long-tail examples for edge-case discoverability.
2. Improve release notes cross-linking for offline readers.

### Nice-to-Have (CAN fix)
1. Add extra operator screenshots for onboarding.
2. Expand FAQ with known troubleshooting paths.

## Appendix A - Evidence Log

{appendix_depth}

## Appendix B - Notes

All findings are reproducible from local validation commands and checked artifacts.
"""


class TestStrategicReviewScaffold:
    def test_creates_strategic_review_artifact(self, tmp_path):
        result = run(STRATEGIC_REVIEW, str(tmp_path))
        assert result.returncode == 0, result.stderr
        assert (tmp_path / ".ideas" / "evaluation-results.md").exists()

    def test_frontmatter_present(self, tmp_path):
        run(STRATEGIC_REVIEW, str(tmp_path))
        content = (tmp_path / ".ideas" / "evaluation-results.md").read_text(encoding="utf-8")
        assert "artifact: evaluation_results" in content
        assert "phase: strategy" in content

    def test_idempotent_no_overwrite(self, tmp_path):
        run(STRATEGIC_REVIEW, str(tmp_path))
        result2 = run(STRATEGIC_REVIEW, str(tmp_path))
        assert result2.returncode != 0

    def test_force_flag_overwrites(self, tmp_path):
        run(STRATEGIC_REVIEW, str(tmp_path))
        result2 = run(STRATEGIC_REVIEW, "--force", str(tmp_path))
        assert result2.returncode == 0

    def test_help_flag(self, tmp_path):
        result = run(STRATEGIC_REVIEW, "--help", cwd=tmp_path)
        assert result.returncode == 0
        assert "Usage:" in result.stdout

    def test_default_dir_is_cwd(self, tmp_path):
        result = run(STRATEGIC_REVIEW, cwd=tmp_path)
        assert result.returncode == 0
        assert (tmp_path / ".ideas" / "evaluation-results.md").exists()

    def test_rejects_symlinked_ideas_dir(self, tmp_path):
        external = tmp_path / "external"
        external.mkdir()
        ideas = tmp_path / ".ideas"
        try:
            ideas.symlink_to(external, target_is_directory=True)
        except OSError as exc:
            pytest.skip(f"Symlink creation is not supported in this environment: {exc}")

        result = run(STRATEGIC_REVIEW, str(tmp_path))
        assert result.returncode != 0
        assert "symlink" in result.stderr.lower()

    def test_rejects_unix_system_directory(self):
        result = run(STRATEGIC_REVIEW, "/")
        assert result.returncode != 0
        assert "system directory" in result.stderr.lower()


class TestStrategicReviewRuntimeConfig:
    def test_runtime_config_defaults(self, tmp_path):
        result = subprocess.run(
            ["python3", str(STRATEGIC_REVIEW_RUNTIME), "--mode", "config", "--project-root", str(tmp_path)],
            capture_output=True,
            text=True,
            timeout=SUBPROCESS_TIMEOUT_SECONDS,
            check=False,
        )
        assert result.returncode == 0, result.stderr
        payload = json.loads(result.stdout)
        assert payload["thresholds"]["green_min_score"] == 4.0
        assert payload["thresholds"]["yellow_min_score"] == 3.0
        assert payload["weights"]["output_quality"] == 0.25
        assert payload["blockers"]["emit_on_bands"] == ["YELLOW", "RED"]


class TestStrategicReviewValidator:
    def test_validator_fails_on_scaffold_with_todo(self, tmp_path):
        run(STRATEGIC_REVIEW, str(tmp_path))
        artifact = tmp_path / ".ideas" / "evaluation-results.md"
        result = run(VALIDATE_STRATEGIC_REVIEW, str(artifact), str(tmp_path))
        assert result.returncode != 0

    def test_validator_passes_on_complete_green_document(self, tmp_path):
        ideas_dir = tmp_path / ".ideas"
        ideas_dir.mkdir(parents=True, exist_ok=True)
        artifact = ideas_dir / "evaluation-results.md"
        artifact.write_text(
            _build_valid_strategic_review(project_name="Validation Demo", reported_band="GREEN"),
            encoding="utf-8",
        )

        result = run(VALIDATE_STRATEGIC_REVIEW, str(artifact), str(tmp_path))
        assert result.returncode == 0, result.stderr
        assert not (ideas_dir / "launch-blockers.md").exists()

    def test_validator_emits_launch_blockers_on_yellow(self, tmp_path):
        ideas_dir = tmp_path / ".ideas"
        ideas_dir.mkdir(parents=True, exist_ok=True)
        artifact = ideas_dir / "evaluation-results.md"
        artifact.write_text(
            _build_valid_strategic_review(
                project_name="Yellow Demo",
                scores={
                    "output_quality": 3.4,
                    "readme_docs_quality": 3.3,
                    "developer_experience": 3.4,
                    "security_trust": 3.5,
                    "competitive_positioning": 3.2,
                    "test_coverage": 3.1,
                },
                blockers=["Fix failing smoke-test path.", "Address ambiguous README setup step."],
                reported_band="YELLOW",
            ),
            encoding="utf-8",
        )

        result = run(VALIDATE_STRATEGIC_REVIEW, str(artifact), str(tmp_path))
        assert result.returncode == 0, result.stderr
        blockers_path = ideas_dir / "launch-blockers.md"
        assert blockers_path.exists()
        blockers_content = blockers_path.read_text(encoding="utf-8")
        assert "Launch Blockers (YELLOW)" in blockers_content
        assert "Fix failing smoke-test path." in blockers_content

    def test_validator_uses_thresholds_from_project_config(self, tmp_path):
        ideas_dir = tmp_path / ".ideas"
        ideas_dir.mkdir(parents=True, exist_ok=True)
        artifact = ideas_dir / "evaluation-results.md"
        artifact.write_text(
            _build_valid_strategic_review(
                project_name="Config Threshold Demo",
                scores={
                    "output_quality": 4.4,
                    "readme_docs_quality": 4.1,
                    "developer_experience": 4.3,
                    "security_trust": 4.4,
                    "competitive_positioning": 4.2,
                    "test_coverage": 4.0,
                },
                blockers=["Raise test confidence for launch candidate."],
                reported_band="YELLOW",
            ),
            encoding="utf-8",
        )

        config_dir = tmp_path / ".specify"
        config_dir.mkdir(parents=True, exist_ok=True)
        (config_dir / "spec-kit.yml").write_text(
            """schema_version: 1
strategic_review:
  thresholds:
    green_min_score: 4.8
    yellow_min_score: 4.0
""",
            encoding="utf-8",
        )

        result = run(VALIDATE_STRATEGIC_REVIEW, str(artifact), str(tmp_path))
        assert result.returncode == 0, result.stderr
        blockers_path = ideas_dir / "launch-blockers.md"
        assert blockers_path.exists()
        assert "YELLOW" in blockers_path.read_text(encoding="utf-8")


@skip_no_pwsh
class TestStrategicReviewPowerShell:
    def test_creates_strategic_review_artifact(self, tmp_path):
        result = run_ps1(STRATEGIC_REVIEW_PS1, str(tmp_path))
        assert result.returncode == 0, result.stderr
        assert (tmp_path / ".ideas" / "evaluation-results.md").exists()

    def test_validator_passes_on_complete_document(self, tmp_path):
        ideas_dir = tmp_path / ".ideas"
        ideas_dir.mkdir(parents=True, exist_ok=True)
        artifact = ideas_dir / "evaluation-results.md"
        artifact.write_text(
            _build_valid_strategic_review(project_name="PowerShell Validation Demo", reported_band="GREEN"),
            encoding="utf-8",
        )

        result = run_ps1(VALIDATE_STRATEGIC_REVIEW_PS1, str(artifact), str(tmp_path))
        assert result.returncode == 0, result.stderr

    def test_validator_emits_blockers_on_red(self, tmp_path):
        ideas_dir = tmp_path / ".ideas"
        ideas_dir.mkdir(parents=True, exist_ok=True)
        artifact = ideas_dir / "evaluation-results.md"
        artifact.write_text(
            _build_valid_strategic_review(
                project_name="PowerShell Red Demo",
                scores={
                    "output_quality": 2.2,
                    "readme_docs_quality": 2.4,
                    "developer_experience": 2.5,
                    "security_trust": 2.1,
                    "competitive_positioning": 2.0,
                    "test_coverage": 2.6,
                },
                blockers=["Resolve critical reliability regression before launch."],
                reported_band="RED",
            ),
            encoding="utf-8",
        )

        result = run_ps1(VALIDATE_STRATEGIC_REVIEW_PS1, str(artifact), str(tmp_path))
        assert result.returncode == 0, result.stderr
        blockers_path = ideas_dir / "launch-blockers.md"
        assert blockers_path.exists()
        assert "RED" in blockers_path.read_text(encoding="utf-8")

    def test_rejects_system_directory(self):
        target = "/" if os.name != "nt" else os.environ.get("SystemRoot", r"C:\Windows")
        result = run_ps1(STRATEGIC_REVIEW_PS1, target)
        assert result.returncode != 0
        assert "system directory" in result.stderr.lower()
