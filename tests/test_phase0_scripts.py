"""Tests for Phase 0 scaffolding scripts: ideate.sh, select.sh, structure.sh (issue #15).

Tests cover:
- Script creates .spec-kit/<artifact>.md from template
- Idempotency: second run exits non-zero if file exists (without --force)
- --force overwrites existing file
- --help flag prints usage
- PROJECT_DIR argument controls target directory
- Created file contains expected YAML frontmatter and section headers
"""

import subprocess
import tempfile
from pathlib import Path

import pytest

SCRIPT_DIR = Path(__file__).parent.parent / "scripts" / "bash"
IDEATE = SCRIPT_DIR / "ideate.sh"
SELECT = SCRIPT_DIR / "select.sh"
STRUCTURE = SCRIPT_DIR / "structure.sh"


def run(script: Path, *args, cwd=None) -> subprocess.CompletedProcess:
    return subprocess.run(
        [str(script), *args],
        capture_output=True,
        text=True,
        cwd=cwd,
    )


# ---------------------------------------------------------------------------
# ideate.sh
# ---------------------------------------------------------------------------


class TestIdeate:
    def test_creates_ideas_backlog(self, tmp_path):
        result = run(IDEATE, str(tmp_path))
        assert result.returncode == 0, result.stderr
        artifact = tmp_path / ".spec-kit" / "ideas_backlog.md"
        assert artifact.exists()

    def test_ideas_backlog_has_frontmatter(self, tmp_path):
        run(IDEATE, str(tmp_path))
        content = (tmp_path / ".spec-kit" / "ideas_backlog.md").read_text()
        assert "artifact: ideas_backlog" in content
        assert "phase: ideate" in content
        assert "schema_version:" in content

    def test_ideas_backlog_has_seed_section(self, tmp_path):
        run(IDEATE, str(tmp_path))
        content = (tmp_path / ".spec-kit" / "ideas_backlog.md").read_text()
        assert "## Seed Ideas" in content
        assert "SCAMPER" in content

    def test_ideas_backlog_has_hmw_section(self, tmp_path):
        run(IDEATE, str(tmp_path))
        content = (tmp_path / ".spec-kit" / "ideas_backlog.md").read_text()
        assert "HMW" in content

    def test_idempotent_no_overwrite(self, tmp_path):
        run(IDEATE, str(tmp_path))
        result2 = run(IDEATE, str(tmp_path))
        assert result2.returncode != 0

    def test_force_flag_overwrites(self, tmp_path):
        run(IDEATE, str(tmp_path))
        result2 = run(IDEATE, "--force", str(tmp_path))
        assert result2.returncode == 0

    def test_help_flag(self, tmp_path):
        result = run(IDEATE, "--help", cwd=tmp_path)
        assert result.returncode == 0
        assert "Usage" in result.stdout or "usage" in result.stdout.lower()

    def test_invalid_dir_exits_nonzero(self, tmp_path):
        result = run(IDEATE, str(tmp_path / "nonexistent_dir"))
        assert result.returncode != 0

    def test_creates_spec_kit_dir(self, tmp_path):
        run(IDEATE, str(tmp_path))
        assert (tmp_path / ".spec-kit").is_dir()

    def test_timestamp_substituted(self, tmp_path):
        run(IDEATE, str(tmp_path))
        content = (tmp_path / ".spec-kit" / "ideas_backlog.md").read_text()
        assert "[ISO_8601_TIMESTAMP]" not in content

    def test_project_name_substituted(self, tmp_path):
        named = tmp_path / "my-project"
        named.mkdir()
        run(IDEATE, str(named))
        content = (named / ".spec-kit" / "ideas_backlog.md").read_text()
        assert "my-project" in content
        assert "[PROJECT_NAME]" not in content

    def test_default_dir_is_cwd(self, tmp_path):
        result = run(IDEATE, cwd=tmp_path)
        assert result.returncode == 0
        assert (tmp_path / ".spec-kit" / "ideas_backlog.md").exists()


# ---------------------------------------------------------------------------
# select.sh
# ---------------------------------------------------------------------------


class TestSelect:
    def test_creates_idea_selection(self, tmp_path):
        result = run(SELECT, str(tmp_path))
        assert result.returncode == 0, result.stderr
        artifact = tmp_path / ".spec-kit" / "idea_selection.md"
        assert artifact.exists()

    def test_idea_selection_has_frontmatter(self, tmp_path):
        run(SELECT, str(tmp_path))
        content = (tmp_path / ".spec-kit" / "idea_selection.md").read_text()
        assert "artifact: idea_selection" in content
        assert "phase: select" in content

    def test_idea_selection_has_airice_table(self, tmp_path):
        run(SELECT, str(tmp_path))
        content = (tmp_path / ".spec-kit" / "idea_selection.md").read_text()
        assert "AI-RICE" in content
        assert "Reach" in content

    def test_idempotent_no_overwrite(self, tmp_path):
        run(SELECT, str(tmp_path))
        result2 = run(SELECT, str(tmp_path))
        assert result2.returncode != 0

    def test_force_flag_overwrites(self, tmp_path):
        run(SELECT, str(tmp_path))
        result2 = run(SELECT, "--force", str(tmp_path))
        assert result2.returncode == 0

    def test_help_flag(self, tmp_path):
        result = run(SELECT, "--help", cwd=tmp_path)
        assert result.returncode == 0
        assert "Usage" in result.stdout or "usage" in result.stdout.lower()

    def test_timestamp_substituted(self, tmp_path):
        run(SELECT, str(tmp_path))
        content = (tmp_path / ".spec-kit" / "idea_selection.md").read_text()
        assert "[ISO_8601_TIMESTAMP]" not in content

    def test_default_dir_is_cwd(self, tmp_path):
        result = run(SELECT, cwd=tmp_path)
        assert result.returncode == 0
        assert (tmp_path / ".spec-kit" / "idea_selection.md").exists()


# ---------------------------------------------------------------------------
# structure.sh
# ---------------------------------------------------------------------------


class TestStructure:
    def test_creates_ai_vision_canvas(self, tmp_path):
        result = run(STRUCTURE, str(tmp_path))
        assert result.returncode == 0, result.stderr
        artifact = tmp_path / ".spec-kit" / "ai_vision_canvas.md"
        assert artifact.exists()

    def test_canvas_has_frontmatter(self, tmp_path):
        run(STRUCTURE, str(tmp_path))
        content = (tmp_path / ".spec-kit" / "ai_vision_canvas.md").read_text()
        assert "artifact: ai_vision_canvas" in content
        assert "phase: structure" in content

    def test_canvas_has_jtbd_section(self, tmp_path):
        run(STRUCTURE, str(tmp_path))
        content = (tmp_path / ".spec-kit" / "ai_vision_canvas.md").read_text()
        assert "JOBS-TO-BE-DONE" in content or "Job Statement" in content

    def test_canvas_has_ai_specific_section(self, tmp_path):
        run(STRUCTURE, str(tmp_path))
        content = (tmp_path / ".spec-kit" / "ai_vision_canvas.md").read_text()
        assert "AI Task" in content or "AI-SPECIFIC" in content

    def test_idempotent_no_overwrite(self, tmp_path):
        run(STRUCTURE, str(tmp_path))
        result2 = run(STRUCTURE, str(tmp_path))
        assert result2.returncode != 0

    def test_force_flag_overwrites(self, tmp_path):
        run(STRUCTURE, str(tmp_path))
        result2 = run(STRUCTURE, "--force", str(tmp_path))
        assert result2.returncode == 0

    def test_help_flag(self, tmp_path):
        result = run(STRUCTURE, "--help", cwd=tmp_path)
        assert result.returncode == 0
        assert "Usage" in result.stdout or "usage" in result.stdout.lower()

    def test_timestamp_substituted(self, tmp_path):
        run(STRUCTURE, str(tmp_path))
        content = (tmp_path / ".spec-kit" / "ai_vision_canvas.md").read_text()
        assert "[ISO_8601_TIMESTAMP]" not in content

    def test_project_name_substituted(self, tmp_path):
        named = tmp_path / "my-ai-project"
        named.mkdir()
        run(STRUCTURE, str(named))
        content = (named / ".spec-kit" / "ai_vision_canvas.md").read_text()
        assert "my-ai-project" in content
        assert "[PROJECT_NAME]" not in content

    def test_default_dir_is_cwd(self, tmp_path):
        result = run(STRUCTURE, cwd=tmp_path)
        assert result.returncode == 0
        assert (tmp_path / ".spec-kit" / "ai_vision_canvas.md").exists()
