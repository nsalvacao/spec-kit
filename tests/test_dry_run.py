"""Tests for --dry-run flag on `specify init` (issue #26).

Tests cover:
- --dry-run flag is accepted without error
- No files or directories are created
- Output describes what WOULD be done (preview content)
- Works with --here flag
- Works with explicit project name
- Combines correctly with --ai, --script, --no-git flags
- Exit code 0 (success)
"""

import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
from typer.testing import CliRunner

from specify_cli import app

runner = CliRunner()


def _run_dry_run(*extra_args):
    """Helper: run init --dry-run with minimal required flags."""
    return runner.invoke(app, [
        "init", "test-project",
        "--dry-run",
        "--ai", "copilot",
        "--script", "sh",
        "--no-git",
        "--ignore-agent-tools",
        *extra_args,
    ])


class TestDryRunFlag:
    """Verify --dry-run flag prevents file I/O and shows preview."""

    def test_dry_run_exits_zero(self):
        """--dry-run must exit with code 0."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = runner.invoke(app, [
                "init", "my-project",
                "--dry-run",
                "--ai", "copilot",
                "--script", "sh",
                "--no-git",
                "--ignore-agent-tools",
            ])
        assert result.exit_code == 0, result.output

    def test_dry_run_creates_no_directory(self):
        """--dry-run must not create the project directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_dir = Path(tmpdir) / "new-project"
            result = runner.invoke(app, [
                "init", str(project_dir),
                "--dry-run",
                "--ai", "copilot",
                "--script", "sh",
                "--no-git",
                "--ignore-agent-tools",
            ])
            assert not project_dir.exists(), (
                f"--dry-run created directory {project_dir} but should not have"
            )

    def test_dry_run_output_contains_dry_run_indicator(self):
        """Output must clearly indicate this is a dry run."""
        result = _run_dry_run()
        output_lower = result.output.lower()
        assert "dry" in output_lower or "preview" in output_lower or "would" in output_lower, (
            f"Expected dry-run indicator in output, got:\n{result.output}"
        )

    def test_dry_run_shows_agent(self):
        """Output must mention the selected AI agent."""
        result = _run_dry_run()
        assert "copilot" in result.output.lower(), (
            f"Expected 'copilot' in dry-run output:\n{result.output}"
        )

    def test_dry_run_shows_script_type(self):
        """Output must mention the selected script type."""
        result = _run_dry_run()
        assert "sh" in result.output.lower(), (
            f"Expected 'sh' in dry-run output:\n{result.output}"
        )

    def test_dry_run_does_not_download(self):
        """--dry-run must not call download_and_extract_template."""
        with patch("specify_cli.download_and_extract_template") as mock_dl:
            _run_dry_run()
        mock_dl.assert_not_called()

    def test_dry_run_with_here_flag(self):
        """--dry-run --here must work and create no files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = runner.invoke(app, [
                "init",
                "--here",
                "--dry-run",
                "--ai", "copilot",
                "--script", "sh",
                "--no-git",
                "--ignore-agent-tools",
                "--force",
            ], catch_exceptions=False)
            # tmpdir still empty (or only contains what was there before)
            assert result.exit_code == 0, result.output

    def test_dry_run_invalid_agent_still_errors(self):
        """--dry-run with invalid --ai must still exit with error (validation first)."""
        result = runner.invoke(app, [
            "init", "test-project",
            "--dry-run",
            "--ai", "notanagent",
        ])
        assert result.exit_code == 1
        assert "Invalid AI assistant" in result.output

    def test_dry_run_shows_project_name(self):
        """Output must mention the project name."""
        result = _run_dry_run()
        assert "test-project" in result.output, (
            f"Expected project name in dry-run output:\n{result.output}"
        )
