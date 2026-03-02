"""Tests for changelog hydrator used by release metadata sync workflow."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


SCRIPT = Path(__file__).parent.parent / "scripts" / "python" / "changelog-hydrator.py"


def run_script(repo_root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        cwd=str(repo_root),
        capture_output=True,
        text=True,
    )


def test_hydrates_placeholder_from_changelog_section(tmp_path: Path) -> None:
    changelog = tmp_path / "CHANGELOG.md"
    body = tmp_path / "release-body.md"

    changelog.write_text(
        """# Changelog

## [Unreleased]

## [0.0.80] - 2026-03-02

### Added

- *No changes documented yet.*

## [0.0.79] - 2026-03-02
""",
        encoding="utf-8",
    )
    body.write_text(
        """Some intro text.

## Changelog

- feat: add native brainstorm command
- test: add regression tests
""",
        encoding="utf-8",
    )

    result = run_script(
        tmp_path,
        "--changelog",
        "CHANGELOG.md",
        "--version",
        "0.0.80",
        "--release-body-file",
        "release-body.md",
        "--json",
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["changed"] is True
    updated = changelog.read_text(encoding="utf-8")
    assert "- feat: add native brainstorm command" in updated
    assert "- test: add regression tests" in updated
    assert "- *No changes documented yet.*" not in updated


def test_no_change_when_placeholder_not_present(tmp_path: Path) -> None:
    changelog = tmp_path / "CHANGELOG.md"
    body = tmp_path / "release-body.md"

    changelog.write_text(
        """# Changelog

## [Unreleased]

## [0.0.80] - 2026-03-02

### Added

- already documented line
""",
        encoding="utf-8",
    )
    body.write_text(
        """## Changelog

- feat: should not replace
""",
        encoding="utf-8",
    )

    result = run_script(
        tmp_path,
        "--changelog",
        "CHANGELOG.md",
        "--version",
        "0.0.80",
        "--release-body-file",
        "release-body.md",
        "--json",
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["changed"] is False
    assert payload["reason"] == "placeholder_not_present"
