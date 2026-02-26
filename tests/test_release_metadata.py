"""Tests for release metadata guard/sync utility (issue #156)."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


SCRIPT = Path(__file__).parent.parent / "scripts" / "python" / "release-metadata.py"


def run_script(repo_root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        cwd=str(repo_root),
        capture_output=True,
        text=True,
    )


def seed_repo(repo_root: Path) -> None:
    (repo_root / ".github").mkdir(parents=True, exist_ok=True)
    (repo_root / ".github" / "release-version-policy.yml").write_text(
        """policy_version: "1"
version:
  canonical_file: "pyproject.toml"
  canonical_pattern: '^version\\s*=\\s*"(?P<version>[0-9]+\\.[0-9]+\\.[0-9]+(?:-fork\\.[0-9]+)?)"\\s*$'
changelog:
  file: "CHANGELOG.md"
  unreleased_heading: "## [Unreleased]"
  release_heading_pattern: '^## \\[(?P<version>[0-9]+\\.[0-9]+\\.[0-9]+(?:-fork\\.[0-9]+)?)\\] - (?P<date>[0-9]{4}-[0-9]{2}-[0-9]{2})$'
monitoring:
  drift_sla_hours: 24
branch_hygiene:
  protected_exact: ["main"]
  protected_prefixes: ["baseline/"]
sync:
  allowlist:
    - "pyproject.toml"
    - "CHANGELOG.md"
""",
        encoding="utf-8",
    )
    (repo_root / "pyproject.toml").write_text(
        """[project]
name = "specify-cli"
version = "0.0.53"
requires-python = ">=3.11"
""",
        encoding="utf-8",
    )
    (repo_root / "CHANGELOG.md").write_text(
        """# Changelog

## [Unreleased]

### Added

- Placeholder

## [0.0.53] - 2026-02-26

### Added

- Previous release
""",
        encoding="utf-8",
    )


def test_sync_updates_pyproject_and_inserts_changelog_heading(tmp_path: Path) -> None:
    seed_repo(tmp_path)

    result = run_script(
        tmp_path,
        "sync",
        "--repo-root",
        str(tmp_path),
        "--policy",
        ".github/release-version-policy.yml",
        "--release-tag",
        "v0.0.54",
        "--release-date",
        "2026-02-27",
        "--json",
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["changed"] is True
    assert sorted(payload["changed_files"]) == ["CHANGELOG.md", "pyproject.toml"]

    pyproject = (tmp_path / "pyproject.toml").read_text(encoding="utf-8")
    changelog = (tmp_path / "CHANGELOG.md").read_text(encoding="utf-8")
    assert 'version = "0.0.54"' in pyproject
    assert "## [0.0.54] - 2026-02-27" in changelog


def test_sync_inserts_release_before_unreleased_content_without_blank_line(tmp_path: Path) -> None:
    seed_repo(tmp_path)
    (tmp_path / "CHANGELOG.md").write_text(
        """# Changelog

## [Unreleased]
### Added
- Keep me in release

## [0.0.53] - 2026-02-26

### Added

- Previous release
""",
        encoding="utf-8",
    )

    result = run_script(
        tmp_path,
        "sync",
        "--repo-root",
        str(tmp_path),
        "--policy",
        ".github/release-version-policy.yml",
        "--release-tag",
        "v0.0.54",
        "--release-date",
        "2026-02-27",
        "--json",
    )

    assert result.returncode == 0, result.stderr
    changelog = (tmp_path / "CHANGELOG.md").read_text(encoding="utf-8")
    assert "## [Unreleased]\n\n## [0.0.54] - 2026-02-27" in changelog
    assert changelog.index("## [0.0.54] - 2026-02-27") < changelog.index("- Keep me in release")


def test_check_fails_when_release_tag_mismatch(tmp_path: Path) -> None:
    seed_repo(tmp_path)

    result = run_script(
        tmp_path,
        "check",
        "--repo-root",
        str(tmp_path),
        "--policy",
        ".github/release-version-policy.yml",
        "--release-tag",
        "v0.0.54",
        "--enforce-release-match",
        "--skip-runtime",
        "--json",
    )

    assert result.returncode != 0
    payload = json.loads(result.stdout)
    assert payload["ok"] is False
    assert "does not match release tag" in " ".join(payload["errors"])


def test_sync_fails_with_invalid_release_date(tmp_path: Path) -> None:
    seed_repo(tmp_path)

    result = run_script(
        tmp_path,
        "sync",
        "--repo-root",
        str(tmp_path),
        "--policy",
        ".github/release-version-policy.yml",
        "--release-tag",
        "v0.0.54",
        "--release-date",
        "2026-02-30",
        "--json",
    )

    assert result.returncode != 0
    assert "Release date must follow 'YYYY-MM-DD'." in result.stderr


def test_check_fails_when_changelog_heading_missing(tmp_path: Path) -> None:
    seed_repo(tmp_path)
    (tmp_path / "CHANGELOG.md").write_text(
        """# Changelog

## [Unreleased]

### Added

- Placeholder
""",
        encoding="utf-8",
    )

    result = run_script(
        tmp_path,
        "check",
        "--repo-root",
        str(tmp_path),
        "--policy",
        ".github/release-version-policy.yml",
        "--skip-runtime",
        "--json",
    )

    assert result.returncode != 0
    payload = json.loads(result.stdout)
    assert payload["ok"] is False
    assert "Missing changelog heading" in " ".join(payload["errors"])


def test_check_passes_when_metadata_is_coherent(tmp_path: Path) -> None:
    seed_repo(tmp_path)

    result = run_script(
        tmp_path,
        "check",
        "--repo-root",
        str(tmp_path),
        "--policy",
        ".github/release-version-policy.yml",
        "--release-tag",
        "v0.0.53",
        "--enforce-release-match",
        "--skip-runtime",
        "--json",
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["ok"] is True
    assert payload["canonical_version"] == "0.0.53"
