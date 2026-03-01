"""Tests for the compliance checker (issue #178)."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

REPO_ROOT = Path(__file__).parent.parent
SCRIPT = REPO_ROOT / "scripts" / "python" / "compliance-checker.py"


def _load_compliance_checker():
    """Load compliance-checker.py as a module (filename has a hyphen)."""
    spec = importlib.util.spec_from_file_location("compliance_checker", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    sys.modules["compliance_checker"] = module  # required so dataclasses can resolve __module__ attribute during class definition
    spec.loader.exec_module(module)
    return module


_cc = _load_compliance_checker()

run_compliance_checks = _cc.run_compliance_checks
_check_license_present = _cc._check_license_present
_check_legal_compliance_markers = _cc._check_legal_compliance_markers
_check_readme_phrases = _cc._check_readme_phrases
_check_trademarks_notice = _cc._check_trademarks_notice
_check_changelog_provenance = _cc._check_changelog_provenance


def run_script(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        capture_output=True,
        text=True,
    )


# ---------------------------------------------------------------------------
# Unit tests — individual checks
# ---------------------------------------------------------------------------


def test_check_license_present_passes_when_file_exists(tmp_path: Path) -> None:
    (tmp_path / "LICENSE").write_text("MIT License\n", encoding="utf-8")
    violations = _check_license_present(tmp_path)
    assert violations == []


def test_check_license_present_fails_when_missing(tmp_path: Path) -> None:
    violations = _check_license_present(tmp_path)
    assert len(violations) == 1
    assert violations[0].check == "license_present"


def test_check_legal_compliance_markers_passes(tmp_path: Path) -> None:
    doc = tmp_path / "docs" / "legal-compliance.md"
    doc.parent.mkdir(parents=True)
    doc.write_text("# Legal\n\n> **Compliance marker**: `legal-compliance:v1`\n", encoding="utf-8")
    violations = _check_legal_compliance_markers(tmp_path)
    assert violations == []


def test_check_legal_compliance_markers_fails_when_doc_missing(tmp_path: Path) -> None:
    violations = _check_legal_compliance_markers(tmp_path)
    assert len(violations) == 1
    assert violations[0].check == "legal_compliance_doc"


def test_check_legal_compliance_markers_fails_when_marker_absent(tmp_path: Path) -> None:
    doc = tmp_path / "docs" / "legal-compliance.md"
    doc.parent.mkdir(parents=True)
    doc.write_text("# Legal\n\nNo marker here.\n", encoding="utf-8")
    violations = _check_legal_compliance_markers(tmp_path)
    assert len(violations) == 1
    assert violations[0].check == "legal_compliance_marker"


def test_check_readme_phrases_passes(tmp_path: Path) -> None:
    readme = tmp_path / "README.md"
    readme.write_text(
        "# Project\n\nThis fork is not affiliated with GitHub.\n\nMIT licensed.\n",
        encoding="utf-8",
    )
    violations = _check_readme_phrases(tmp_path)
    assert violations == []


def test_check_readme_phrases_fails_when_affiliation_missing(tmp_path: Path) -> None:
    readme = tmp_path / "README.md"
    readme.write_text("# Project\n\nMIT licensed.\n", encoding="utf-8")
    violations = _check_readme_phrases(tmp_path)
    assert any(v.check == "readme_required_phrase" for v in violations)
    assert any("not affiliated with github" in v.message.lower() for v in violations)


def test_check_readme_phrases_fails_when_mit_missing(tmp_path: Path) -> None:
    readme = tmp_path / "README.md"
    readme.write_text(
        "# Project\n\nThis fork is not affiliated with GitHub.\n", encoding="utf-8"
    )
    violations = _check_readme_phrases(tmp_path)
    assert any("mit" in v.message.lower() for v in violations)


def test_check_readme_phrases_accepts_mit_license_across_line_breaks(tmp_path: Path) -> None:
    readme = tmp_path / "README.md"
    readme.write_text(
        "# Project\n\nThis fork is not affiliated with GitHub.\n\nMIT\nLicense.\n",
        encoding="utf-8",
    )
    violations = _check_readme_phrases(tmp_path)
    assert violations == []


def test_check_trademarks_notice_passes(tmp_path: Path) -> None:
    doc = tmp_path / "docs" / "trademarks.md"
    doc.parent.mkdir(parents=True)
    doc.write_text("GitHub® is used for attribution only.\n", encoding="utf-8")
    violations = _check_trademarks_notice(tmp_path)
    assert violations == []


def test_check_trademarks_notice_fails_when_doc_missing(tmp_path: Path) -> None:
    violations = _check_trademarks_notice(tmp_path)
    assert len(violations) == 1
    assert violations[0].check == "trademarks_doc"


def test_check_trademarks_notice_fails_when_phrase_absent(tmp_path: Path) -> None:
    doc = tmp_path / "docs" / "trademarks.md"
    doc.parent.mkdir(parents=True)
    doc.write_text("GitHub® trademark.\n", encoding="utf-8")
    violations = _check_trademarks_notice(tmp_path)
    assert len(violations) == 1
    assert violations[0].check == "trademarks_notice"


def test_check_changelog_provenance_passes_with_no_intake_entries(tmp_path: Path) -> None:
    changelog = tmp_path / "CHANGELOG.md"
    changelog.write_text("# Changelog\n\n## [1.0.0]\n\n- Regular fix\n", encoding="utf-8")
    violations = _check_changelog_provenance(tmp_path)
    assert violations == []


def test_check_changelog_provenance_passes_with_provenance_line(tmp_path: Path) -> None:
    changelog = tmp_path / "CHANGELOG.md"
    changelog.write_text(
        "# Changelog\n\n"
        "## [1.0.0]\n\n"
        "- **Upstream PR #42: some fix**\n"
        "  - Description of fix\n"
        "  - Source PR: https://github.com/github/spec-kit/pull/42\n",
        encoding="utf-8",
    )
    violations = _check_changelog_provenance(tmp_path)
    assert violations == []


def test_check_changelog_provenance_fails_when_provenance_missing(tmp_path: Path) -> None:
    changelog = tmp_path / "CHANGELOG.md"
    changelog.write_text(
        "# Changelog\n\n"
        "## [1.0.0]\n\n"
        "- **Upstream PR #42: some fix**\n"
        "  - Description without Source PR line\n",
        encoding="utf-8",
    )
    violations = _check_changelog_provenance(tmp_path)
    assert len(violations) == 1
    assert violations[0].check == "changelog_provenance"


def test_check_changelog_provenance_passes_when_no_changelog(tmp_path: Path) -> None:
    # Missing CHANGELOG is not a compliance violation (changelog may be optional)
    violations = _check_changelog_provenance(tmp_path)
    assert violations == []


# ---------------------------------------------------------------------------
# Integration test — run_compliance_checks on a valid fixture
# ---------------------------------------------------------------------------


def _make_valid_repo(tmp_path: Path) -> Path:
    """Create a minimal valid repository fixture."""
    (tmp_path / "LICENSE").write_text("MIT License\nCopyright GitHub, Inc.\n", encoding="utf-8")
    (tmp_path / "README.md").write_text(
        "# Project\n\nThis fork is not affiliated with GitHub. MIT licensed.\n",
        encoding="utf-8",
    )
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "legal-compliance.md").write_text(
        "> **Compliance marker**: `legal-compliance:v1`\n",
        encoding="utf-8",
    )
    (docs / "trademarks.md").write_text(
        "GitHub® used for attribution only.\n",
        encoding="utf-8",
    )
    (tmp_path / "CHANGELOG.md").write_text(
        "## [1.0.0]\n\n- Fix something\n",
        encoding="utf-8",
    )
    return tmp_path


def test_run_compliance_checks_passes_for_valid_fixture(tmp_path: Path) -> None:
    repo = _make_valid_repo(tmp_path)
    result = run_compliance_checks(repo)
    assert result.ok is True
    assert result.violations == []


def test_run_compliance_checks_fails_for_missing_license(tmp_path: Path) -> None:
    _make_valid_repo(tmp_path)
    (tmp_path / "LICENSE").unlink()
    result = run_compliance_checks(tmp_path)
    assert result.ok is False
    assert any(v.check == "license_present" for v in result.violations)


def test_run_compliance_checks_passes_for_actual_repo() -> None:
    """Verify the actual repository passes all compliance checks."""
    result = run_compliance_checks(REPO_ROOT)
    assert result.ok is True, (
        "Compliance violations in actual repo:\n"
        + "\n".join(f"  [{v.check}] {v.path}: {v.message}" for v in result.violations)
    )


# ---------------------------------------------------------------------------
# Script invocation tests
# ---------------------------------------------------------------------------


def test_script_check_succeeds_for_actual_repo() -> None:
    result = run_script("check", "--repo-root", str(REPO_ROOT))
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["ok"] is True
    assert payload["violations"] == []


def test_script_check_fails_for_missing_license(tmp_path: Path) -> None:
    _make_valid_repo(tmp_path)
    (tmp_path / "LICENSE").unlink()
    result = run_script("check", "--repo-root", str(tmp_path))
    assert result.returncode != 0
    payload = json.loads(result.stdout)
    assert payload["ok"] is False
    assert any(v["check"] == "license_present" for v in payload["violations"])


def test_script_check_fails_for_missing_affiliation_statement(tmp_path: Path) -> None:
    _make_valid_repo(tmp_path)
    (tmp_path / "README.md").write_text("# Project\n\nMIT licensed.\n", encoding="utf-8")
    result = run_script("check", "--repo-root", str(tmp_path))
    assert result.returncode != 0
    payload = json.loads(result.stdout)
    assert payload["ok"] is False
    assert any(v["check"] == "readme_required_phrase" for v in payload["violations"])


def test_script_check_outputs_valid_json(tmp_path: Path) -> None:
    _make_valid_repo(tmp_path)
    result = run_script("check", "--repo-root", str(tmp_path))
    payload = json.loads(result.stdout)
    assert "ok" in payload
    assert "checks_run" in payload
    assert "violations" in payload
