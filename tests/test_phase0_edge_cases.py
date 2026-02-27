"""Phase 0 edge-case tests (issue #33).

Covers:
1. 1-seed workflow boundary — ideate.sh produces a structurally valid ideas_backlog.md
2. 10+ seeds workflow — large idea sets handled without truncation or crash
3. Skip-phase scenario — select.sh without prior ideate exits with a clear actionable error
4. Partial/interrupted state init — state.yaml is not left corrupt
"""

import shutil
import subprocess
from pathlib import Path

import pytest
import yaml

SCRIPT_DIR = Path(__file__).parent.parent / "scripts" / "bash"
PS1_DIR = Path(__file__).parent.parent / "scripts" / "powershell"

IDEATE = SCRIPT_DIR / "ideate.sh"
SELECT = SCRIPT_DIR / "select.sh"
STATE_INIT = SCRIPT_DIR / "state-init.sh"

IDEATE_PS1 = PS1_DIR / "ideate.ps1"
SELECT_PS1 = PS1_DIR / "select.ps1"

PWSH = shutil.which("pwsh")
skip_no_pwsh = pytest.mark.skipif(PWSH is None, reason="pwsh not available")


def run(script: Path, *args, cwd=None) -> subprocess.CompletedProcess:
    return subprocess.run(
        [str(script), *args],
        capture_output=True,
        text=True,
        cwd=cwd,
    )


def run_ps1(script: Path, *args, cwd=None) -> subprocess.CompletedProcess:
    return subprocess.run(
        [PWSH, "-NonInteractive", "-File", str(script), *args],
        capture_output=True,
        text=True,
        cwd=cwd,
    )


# ---------------------------------------------------------------------------
# 1. One-seed workflow boundary
# ---------------------------------------------------------------------------


class TestOneSeedWorkflow:
    """Boundary condition: ideate.sh produces a file suitable for a 1-seed workflow."""

    def test_ideate_produces_valid_frontmatter(self, tmp_path):
        """Generated ideas_backlog.md must have correct YAML frontmatter."""
        result = run(IDEATE, str(tmp_path))
        assert result.returncode == 0, result.stderr
        content = (tmp_path / ".spec-kit" / "ideas_backlog.md").read_text()
        assert "artifact: ideas_backlog" in content
        assert "phase: ideate" in content
        assert "schema_version:" in content

    def test_ideate_produces_seed_section(self, tmp_path):
        """Generated file includes a Seed Ideas section for user to fill in."""
        run(IDEATE, str(tmp_path))
        content = (tmp_path / ".spec-kit" / "ideas_backlog.md").read_text()
        assert "## Seed Ideas" in content
        assert "**Tag**: SEED" in content

    def test_single_seed_file_is_structurally_valid(self, tmp_path):
        """A hand-crafted 1-seed ideas_backlog.md has the required frontmatter and tag."""
        spec_kit = tmp_path / ".spec-kit"
        spec_kit.mkdir()
        seed_content = (
            "---\n"
            "artifact: ideas_backlog\n"
            "phase: ideate\n"
            'schema_version: "1.0"\n'
            "generated: 2024-01-01T00:00:00Z\n"
            "seed_count: 1\n"
            "total_count: 1\n"
            "---\n"
            "\n"
            "# Ideas Backlog: one-seed-project\n"
            "\n"
            "## Seed Ideas (User-Provided)\n"
            "\n"
            "### Idea S1\n"
            "\n"
            "**Text**: A single idea about improving AI data pipelines.\n"
            "**Tag**: SEED\n"
            "**Generated**: 2024-01-01T00:00:00Z\n"
        )
        backlog = spec_kit / "ideas_backlog.md"
        backlog.write_text(seed_content)
        content = backlog.read_text()
        assert "artifact: ideas_backlog" in content
        assert "seed_count: 1" in content
        assert "**Tag**: SEED" in content
        assert content.count("**Tag**: SEED") == 1


# ---------------------------------------------------------------------------
# 2. Large idea set (10+ seeds)
# ---------------------------------------------------------------------------


class TestLargeIdeaSet:
    """10+ seed ideas can be written and read back without truncation or crash."""

    def test_ideate_succeeds_with_long_project_name(self, tmp_path):
        """ideate.sh does not crash on project directories with long names."""
        long_name = tmp_path / ("a" * 80)
        long_name.mkdir()
        result = run(IDEATE, str(long_name))
        assert result.returncode == 0, result.stderr
        assert (long_name / ".spec-kit" / "ideas_backlog.md").exists()

    def test_large_ideas_backlog_survives_round_trip(self, tmp_path):
        """An ideas_backlog.md with 12 seed ideas can be written and read back intact."""
        spec_kit = tmp_path / ".spec-kit"
        spec_kit.mkdir()
        lines = [
            "---",
            "artifact: ideas_backlog",
            "phase: ideate",
            'schema_version: "1.0"',
            "generated: 2024-01-01T00:00:00Z",
            "seed_count: 12",
            "total_count: 12",
            "---",
            "",
            "# Ideas Backlog: large-idea-project",
            "",
            "## Seed Ideas (User-Provided)",
        ]
        for i in range(1, 13):
            lines += [
                "",
                f"### Idea S{i}",
                "",
                f"**Text**: Seed idea number {i} covering AI scenario {i}.",
                "**Tag**: SEED",
                "**Generated**: 2024-01-01T00:00:00Z",
                "",
                "---",
            ]
        content = "\n".join(lines)
        backlog = spec_kit / "ideas_backlog.md"
        backlog.write_text(content)
        readback = backlog.read_text()
        assert readback.count("**Tag**: SEED") == 12
        assert "seed_count: 12" in readback
        assert len(readback) == len(content)

    def test_large_ideas_backlog_no_truncation(self, tmp_path):
        """Writing 15 seeds does not truncate or lose content."""
        spec_kit = tmp_path / ".spec-kit"
        spec_kit.mkdir()
        seeds = "\n".join(
            f"### Idea S{i}\n\n**Text**: Idea {i}.\n**Tag**: SEED\n**Generated**: 2024-01-01T00:00:00Z\n\n---"
            for i in range(1, 16)
        )
        content = f"---\nartifact: ideas_backlog\nphase: ideate\n---\n\n{seeds}"
        backlog = spec_kit / "ideas_backlog.md"
        backlog.write_text(content)
        readback = backlog.read_text()
        assert readback.count("**Tag**: SEED") == 15


# ---------------------------------------------------------------------------
# 3. Skip-phase scenario
# ---------------------------------------------------------------------------


class TestSkipPhase:
    """select.sh must refuse to run when ideas_backlog.md is missing."""

    def test_select_without_ideate_exits_nonzero(self, tmp_path):
        """select.sh exits with a non-zero code when ideas_backlog.md is absent."""
        result = run(SELECT, str(tmp_path))
        assert result.returncode != 0

    def test_select_without_ideate_error_mentions_ideate(self, tmp_path):
        """Error output from select.sh without prior ideate references 'ideate'."""
        result = run(SELECT, str(tmp_path))
        combined = result.stderr + result.stdout
        assert "ideate" in combined.lower()

    def test_select_without_ideate_error_mentions_ideas_backlog(self, tmp_path):
        """Error output from select.sh without prior ideate references 'ideas_backlog'."""
        result = run(SELECT, str(tmp_path))
        combined = result.stderr + result.stdout
        assert "ideas_backlog" in combined

    def test_select_succeeds_after_ideate(self, tmp_path):
        """select.sh succeeds once ideate.sh has been run first."""
        run(IDEATE, str(tmp_path))
        result = run(SELECT, str(tmp_path))
        assert result.returncode == 0, result.stderr

    @skip_no_pwsh
    def test_select_ps1_without_ideate_exits_nonzero(self, tmp_path):
        """select.ps1 exits with a non-zero code when ideas_backlog.md is absent."""
        result = run_ps1(SELECT_PS1, str(tmp_path))
        assert result.returncode != 0

    @skip_no_pwsh
    def test_select_ps1_without_ideate_error_mentions_ideate(self, tmp_path):
        """select.ps1 error output references 'ideate' when prerequisite is missing."""
        result = run_ps1(SELECT_PS1, str(tmp_path))
        combined = result.stderr + result.stdout
        assert "ideate" in combined.lower()


# ---------------------------------------------------------------------------
# 4. Partial / interrupted state init
# ---------------------------------------------------------------------------


class TestStateInitSafety:
    """state-init.sh must not leave state.yaml corrupt."""

    def test_fresh_run_produces_valid_yaml(self, tmp_path):
        """state-init.sh creates a parseable YAML file on a fresh directory."""
        result = run(STATE_INIT, cwd=tmp_path)
        assert result.returncode == 0, result.stderr
        state_file = tmp_path / ".spec-kit" / "state.yaml"
        assert state_file.exists()
        data = yaml.safe_load(state_file.read_text())
        assert isinstance(data, dict)
        assert "workflow_version" in data
        assert "current_phase" in data

    def test_existing_state_yaml_not_overwritten(self, tmp_path):
        """state-init.sh does not overwrite an already-initialised state.yaml."""
        run(STATE_INIT, cwd=tmp_path)
        state_file = tmp_path / ".spec-kit" / "state.yaml"
        first_content = state_file.read_text()
        result = run(STATE_INIT, cwd=tmp_path)
        assert result.returncode == 0, result.stderr
        assert state_file.read_text() == first_content

    def test_partial_state_yaml_preserved_not_overwritten(self, tmp_path):
        """A partially-written state.yaml is preserved, not silently overwritten."""
        spec_kit = tmp_path / ".spec-kit"
        spec_kit.mkdir()
        partial_content = "workflow_version: '1.0'\ncurrent_phase: ideate\n"
        (spec_kit / "state.yaml").write_text(partial_content)
        result = run(STATE_INIT, cwd=tmp_path)
        assert result.returncode == 0, result.stderr
        assert (spec_kit / "state.yaml").read_text() == partial_content
        assert "already exists" in result.stdout

    def test_state_yaml_written_atomically_contains_all_keys(self, tmp_path):
        """state.yaml written by state-init.sh contains all required top-level keys."""
        run(STATE_INIT, cwd=tmp_path)
        data = yaml.safe_load((tmp_path / ".spec-kit" / "state.yaml").read_text())
        required_keys = [
            "workflow_version",
            "current_phase",
            "phases_completed",
            "phases_in_progress",
            "artifacts",
            "profile",
            "violations",
        ]
        for key in required_keys:
            assert key in data, f"Missing key '{key}' in state.yaml"
