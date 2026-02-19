from pathlib import Path

import pytest

from specify_cli.__init__ import detect_existing_specify_state


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
