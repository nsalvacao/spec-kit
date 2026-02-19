"""Tests for --keep-memory constitution preservation behavior."""

import zipfile
from pathlib import Path

from specify_cli import download_and_extract_template


def _create_local_template_zip(
    local_dir: Path,
    *,
    ai_assistant: str = "copilot",
    script_type: str = "sh",
    files: dict[str, str],
) -> Path:
    """Create a local template zip matching the expected filename pattern."""
    local_dir.mkdir(parents=True, exist_ok=True)
    zip_path = local_dir / f"spec-kit-template-{ai_assistant}-{script_type}-0.0.34.zip"
    with zipfile.ZipFile(zip_path, "w") as zip_ref:
        # Use a nested top-level directory to mirror release archive structure.
        root = "spec-kit-template-root"
        for rel_path, content in files.items():
            zip_ref.writestr(f"{root}/{rel_path}", content)
    return zip_path


def test_keep_memory_preserves_existing_constitution(tmp_path: Path):
    """preserve_constitution=True should keep existing .specify/memory/constitution.md."""
    project_path = tmp_path / "project"
    project_path.mkdir()
    constitution_path = project_path / ".specify" / "memory" / "constitution.md"
    constitution_path.parent.mkdir(parents=True, exist_ok=True)
    constitution_path.write_text("existing constitution", encoding="utf-8")

    local_dir = tmp_path / ".genreleases"
    _create_local_template_zip(
        local_dir,
        files={
            ".specify/memory/constitution.md": "template constitution",
            ".specify/scripts/setup.sh": "#!/usr/bin/env bash\necho setup\n",
        },
    )

    download_and_extract_template(
        project_path=project_path,
        ai_assistant="copilot",
        script_type="sh",
        is_current_dir=True,
        verbose=False,
        preserve_constitution=True,
        local_dir=local_dir,
    )

    assert constitution_path.read_text(encoding="utf-8") == "existing constitution"
    assert (project_path / ".specify" / "scripts" / "setup.sh").exists()


def test_keep_memory_false_overwrites_existing_constitution(tmp_path: Path):
    """preserve_constitution=False should overwrite existing constitution from template."""
    project_path = tmp_path / "project"
    project_path.mkdir()
    constitution_path = project_path / ".specify" / "memory" / "constitution.md"
    constitution_path.parent.mkdir(parents=True, exist_ok=True)
    constitution_path.write_text("existing constitution", encoding="utf-8")

    local_dir = tmp_path / ".genreleases"
    _create_local_template_zip(
        local_dir,
        files={
            ".specify/memory/constitution.md": "template constitution",
        },
    )

    download_and_extract_template(
        project_path=project_path,
        ai_assistant="copilot",
        script_type="sh",
        is_current_dir=True,
        verbose=False,
        preserve_constitution=False,
        local_dir=local_dir,
    )

    assert constitution_path.read_text(encoding="utf-8") == "template constitution"
