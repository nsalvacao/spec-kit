"""Tests for project config bootstrap during initialization."""

from pathlib import Path

import pytest

from specify_cli import ensure_project_config_from_template


def test_ensure_project_config_from_template_copies_when_missing(tmp_path: Path):
    project_path = tmp_path / "project"
    template_path = project_path / ".specify" / "templates" / "spec-kit-config-template.yml"
    template_path.parent.mkdir(parents=True, exist_ok=True)
    template_path.write_text("schema_version: 1\nscope_detection: {}\n", encoding="utf-8")

    ensure_project_config_from_template(project_path)

    generated = project_path / ".specify" / "spec-kit.yml"
    assert generated.exists()
    assert generated.read_text(encoding="utf-8") == template_path.read_text(encoding="utf-8")


def test_ensure_project_config_from_template_preserves_existing(tmp_path: Path):
    project_path = tmp_path / "project"
    generated = project_path / ".specify" / "spec-kit.yml"
    template_path = project_path / ".specify" / "templates" / "spec-kit-config-template.yml"

    generated.parent.mkdir(parents=True, exist_ok=True)
    template_path.parent.mkdir(parents=True, exist_ok=True)
    generated.write_text("schema_version: 1\nscope_detection:\n  work_items_multiplier: 2\n", encoding="utf-8")
    template_path.write_text("schema_version: 1\nscope_detection:\n  work_items_multiplier: 9\n", encoding="utf-8")

    ensure_project_config_from_template(project_path)

    assert "work_items_multiplier: 2" in generated.read_text(encoding="utf-8")


@pytest.mark.skipif(not hasattr(Path, "symlink_to"), reason="symlink support unavailable")
def test_ensure_project_config_from_template_skips_symlinked_specify(tmp_path: Path):
    project_path = tmp_path / "project"
    project_path.mkdir()
    external_specify = tmp_path / "external-specify"
    template_path = external_specify / "templates" / "spec-kit-config-template.yml"
    template_path.parent.mkdir(parents=True, exist_ok=True)
    template_path.write_text("schema_version: 1\nscope_detection: {}\n", encoding="utf-8")

    (project_path / ".specify").symlink_to(external_specify, target_is_directory=True)

    ensure_project_config_from_template(project_path)

    assert not (external_specify / "spec-kit.yml").exists()
