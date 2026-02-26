"""Tests for manifest-driven version orchestration utility (issue #165)."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


SCRIPT = Path(__file__).parent.parent / "scripts" / "python" / "version-orchestrator.py"


def run_script(repo_root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        cwd=str(repo_root),
        capture_output=True,
        text=True,
    )


def seed_repo(repo_root: Path, *, canonical_version: str, target_version: str) -> None:
    (repo_root / ".github").mkdir(parents=True, exist_ok=True)
    (repo_root / ".github" / "version-map.yml").write_text(
        """version_map_version: "1"
canonical:
  file: "pyproject.toml"
  pattern: '^version\\s*=\\s*"(?P<version>[0-9]+\\.[0-9]+\\.[0-9]+(?:-fork\\.[0-9]+)?)"\\s*$'
targets:
  - file: "uv.lock"
    pattern: '(?ms)^\\[\\[package\\]\\]\\nname = "specify-cli"\\nversion = "(?P<version>[0-9]+\\.[0-9]+\\.[0-9]+(?:-fork\\.[0-9]+)?)"'
    expected_matches: 1
changelog:
  file: "CHANGELOG.md"
  unreleased_heading: "## [Unreleased]"
  release_heading_pattern: '^## \\[(?P<version>[0-9]+\\.[0-9]+\\.[0-9]+(?:-fork\\.[0-9]+)?)\\] - (?P<date>[0-9]{4}-[0-9]{2}-[0-9]{2})$'
  scaffold_heading: "### Added"
  scaffold_placeholder: "- *No changes documented yet.*"
runtime:
  command:
    - "uv"
    - "run"
    - "specify"
    - "version"
  version_pattern: 'CLI Version\\s+(?P<version>[0-9]+\\.[0-9]+\\.[0-9]+(?:-fork\\.[0-9]+)?)'
tagging:
  tag_pattern: '^v(?P<version>[0-9]+\\.[0-9]+\\.[0-9]+(?:-fork\\.[0-9]+)?)$'
sync:
  allowlist:
    - "pyproject.toml"
    - "uv.lock"
    - "CHANGELOG.md"
""",
        encoding="utf-8",
    )
    (repo_root / "pyproject.toml").write_text(
        f"""[project]
name = "specify-cli"
version = "{canonical_version}"
requires-python = ">=3.11"
""",
        encoding="utf-8",
    )
    (repo_root / "uv.lock").write_text(
        f"""[[package]]
name = "specify-cli"
version = "{target_version}"
source = {{ editable = "." }}
""",
        encoding="utf-8",
    )
    (repo_root / "CHANGELOG.md").write_text(
        f"""# Changelog

## [Unreleased]

## [{canonical_version}] - 2026-02-26

### Added

- Previous release entry
""",
        encoding="utf-8",
    )


def test_check_passes_when_versions_are_coherent(tmp_path: Path) -> None:
    seed_repo(tmp_path, canonical_version="0.0.53", target_version="0.0.53")
    result = run_script(
        tmp_path,
        "check",
        "--repo-root",
        str(tmp_path),
        "--map",
        ".github/version-map.yml",
        "--skip-runtime",
        "--json",
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["ok"] is True
    assert payload["canonical_version"] == "0.0.53"


def test_check_fails_when_target_version_drifts(tmp_path: Path) -> None:
    seed_repo(tmp_path, canonical_version="0.0.53", target_version="0.0.52")
    result = run_script(
        tmp_path,
        "check",
        "--repo-root",
        str(tmp_path),
        "--map",
        ".github/version-map.yml",
        "--skip-runtime",
        "--json",
    )

    assert result.returncode != 0
    payload = json.loads(result.stdout)
    assert payload["ok"] is False
    assert "Target 'uv.lock' version '0.0.52'" in " ".join(payload["errors"])


def test_check_fails_when_release_tag_mismatch(tmp_path: Path) -> None:
    seed_repo(tmp_path, canonical_version="0.0.53", target_version="0.0.53")
    result = run_script(
        tmp_path,
        "check",
        "--repo-root",
        str(tmp_path),
        "--map",
        ".github/version-map.yml",
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


def test_bump_patch_updates_canonical_target_and_changelog(tmp_path: Path) -> None:
    seed_repo(tmp_path, canonical_version="0.0.53", target_version="0.0.53")
    result = run_script(
        tmp_path,
        "bump",
        "--repo-root",
        str(tmp_path),
        "--map",
        ".github/version-map.yml",
        "--part",
        "patch",
        "--release-date",
        "2026-02-27",
        "--json",
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["next_version"] == "0.0.54"
    assert sorted(payload["changed_files"]) == ["CHANGELOG.md", "pyproject.toml", "uv.lock"]

    assert 'version = "0.0.54"' in (tmp_path / "pyproject.toml").read_text(encoding="utf-8")
    assert 'version = "0.0.54"' in (tmp_path / "uv.lock").read_text(encoding="utf-8")
    assert "## [0.0.54] - 2026-02-27" in (tmp_path / "CHANGELOG.md").read_text(encoding="utf-8")


def test_bump_dry_run_reports_diff_without_writing_files(tmp_path: Path) -> None:
    seed_repo(tmp_path, canonical_version="0.0.53", target_version="0.0.53")
    result = run_script(
        tmp_path,
        "bump",
        "--repo-root",
        str(tmp_path),
        "--map",
        ".github/version-map.yml",
        "--part",
        "patch",
        "--dry-run",
        "--include-diff",
        "--json",
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["dry_run"] is True
    assert payload["changed"] is True
    assert "b/pyproject.toml" in payload["diff_preview"]
    assert 'version = "0.0.53"' in (tmp_path / "pyproject.toml").read_text(encoding="utf-8")


def test_bump_fails_for_invalid_release_date(tmp_path: Path) -> None:
    seed_repo(tmp_path, canonical_version="0.0.53", target_version="0.0.53")
    result = run_script(
        tmp_path,
        "bump",
        "--repo-root",
        str(tmp_path),
        "--map",
        ".github/version-map.yml",
        "--part",
        "patch",
        "--release-date",
        "2026-02-30",
        "--json",
    )

    assert result.returncode != 0
    assert "Release date must follow 'YYYY-MM-DD'." in result.stderr


def test_sync_from_release_tag_updates_all_mapped_files(tmp_path: Path) -> None:
    seed_repo(tmp_path, canonical_version="0.0.53", target_version="0.0.53")
    result = run_script(
        tmp_path,
        "sync",
        "--repo-root",
        str(tmp_path),
        "--map",
        ".github/version-map.yml",
        "--release-tag",
        "v0.0.60",
        "--release-date",
        "2026-02-28",
        "--json",
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["next_version"] == "0.0.60"
    assert sorted(payload["changed_files"]) == ["CHANGELOG.md", "pyproject.toml", "uv.lock"]
    assert 'version = "0.0.60"' in (tmp_path / "pyproject.toml").read_text(encoding="utf-8")
    assert 'version = "0.0.60"' in (tmp_path / "uv.lock").read_text(encoding="utf-8")


def test_sync_requires_exactly_one_target_selector(tmp_path: Path) -> None:
    seed_repo(tmp_path, canonical_version="0.0.53", target_version="0.0.53")
    result = run_script(
        tmp_path,
        "sync",
        "--repo-root",
        str(tmp_path),
        "--map",
        ".github/version-map.yml",
        "--json",
    )

    assert result.returncode != 0
    assert "Provide one and only one of --target-version or --release-tag." in result.stderr


def test_check_rejects_runtime_command_with_path_executable(tmp_path: Path) -> None:
    seed_repo(tmp_path, canonical_version="0.0.53", target_version="0.0.53")
    map_path = tmp_path / ".github" / "version-map.yml"
    map_path.write_text(
        map_path.read_text(encoding="utf-8").replace('- "uv"', '- "/bin/uv"'),
        encoding="utf-8",
    )

    result = run_script(
        tmp_path,
        "check",
        "--repo-root",
        str(tmp_path),
        "--map",
        ".github/version-map.yml",
        "--skip-runtime",
        "--json",
    )

    assert result.returncode != 0
    assert "Runtime command executable must be a tool name, not a path." in result.stderr
