import os
from pathlib import Path

import pytest

from specify_cli.__init__ import (
    detect_existing_specify_state,
    ensure_constitution_from_template,
    ensure_executable_scripts,
)


def test_detect_existing_specify_state_missing_path(tmp_path: Path) -> None:
    has_existing, is_symlink = detect_existing_specify_state(tmp_path / ".specify")
    assert has_existing is False
    assert is_symlink is False


def test_detect_existing_specify_state_empty_directory(tmp_path: Path) -> None:
    specify_dir = tmp_path / ".specify"
    specify_dir.mkdir()

    has_existing, is_symlink = detect_existing_specify_state(specify_dir)
    assert has_existing is False
    assert is_symlink is False


def test_detect_existing_specify_state_non_empty_directory(tmp_path: Path) -> None:
    specify_dir = tmp_path / ".specify"
    specify_dir.mkdir()
    (specify_dir / "constitution.md").write_text("# Test Constitution\n")

    has_existing, is_symlink = detect_existing_specify_state(specify_dir)
    assert has_existing is True
    assert is_symlink is False


@pytest.mark.skipif(not hasattr(Path, "symlink_to"), reason="symlink support unavailable")
def test_detect_existing_specify_state_symlink(tmp_path: Path) -> None:
    target = tmp_path / "real-specify"
    target.mkdir()
    (target / "spec.md").write_text("data\n")

    link_path = tmp_path / ".specify"
    link_path.symlink_to(target, target_is_directory=True)

    has_existing, is_symlink = detect_existing_specify_state(link_path)
    assert has_existing is True
    assert is_symlink is True


@pytest.mark.skipif(not hasattr(Path, "symlink_to"), reason="symlink support unavailable")
def test_ensure_constitution_from_template_skips_symlinked_specify(tmp_path: Path) -> None:
    project_path = tmp_path / "project"
    project_path.mkdir()
    external_specify = tmp_path / "external-specify"
    template_path = external_specify / "templates" / "constitution-template.md"
    template_path.parent.mkdir(parents=True, exist_ok=True)
    template_path.write_text("# Constitution template\n", encoding="utf-8")

    (project_path / ".specify").symlink_to(external_specify, target_is_directory=True)

    ensure_constitution_from_template(project_path)

    assert not (external_specify / "memory" / "constitution.md").exists()


@pytest.mark.skipif(
    os.name == "nt" or not hasattr(Path, "symlink_to"),
    reason="symlink + chmod semantics require POSIX symlink support",
)
def test_ensure_executable_scripts_skips_symlinked_specify(tmp_path: Path) -> None:
    project_path = tmp_path / "project"
    project_path.mkdir()
    external_specify = tmp_path / "external-specify"
    script_path = external_specify / "scripts" / "validate.sh"
    script_path.parent.mkdir(parents=True, exist_ok=True)
    script_path.write_text("#!/usr/bin/env bash\necho ok\n", encoding="utf-8")
    script_path.chmod(0o644)

    (project_path / ".specify").symlink_to(external_specify, target_is_directory=True)

    ensure_executable_scripts(project_path)

    assert (script_path.stat().st_mode & 0o777) == 0o644
