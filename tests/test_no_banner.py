"""Tests for --no-banner flag on `specify init` (issue #27).

Tests cover:
- --no-banner suppresses the ASCII art banner in init output
- Normal init (without --no-banner) shows the banner
- --no-banner works with --dry-run
- --no-banner works with --here flag
- --no-banner does not affect functionality (files still created)
- --no-banner works alongside other flags (--ai, --script, --no-git)
- Exit code 0 when --no-banner used
"""

import tempfile
from pathlib import Path
from unittest.mock import patch

from typer.testing import CliRunner

from specify_cli import app

runner = CliRunner()

# Distinctive text that only appears in the banner (not in regular output)
BANNER_MARKER = "Nexo Spec Kit"


def _run_init(*extra_args):
    """Helper: run init with minimal required flags."""
    return runner.invoke(app, [
        "init", "test-project",
        "--ai", "copilot",
        "--script", "sh",
        "--no-git",
        "--ignore-agent-tools",
        *extra_args,
    ])


class TestNoBannerFlag:
    """Verify --no-banner suppresses ASCII art in CI-friendly mode."""

    def test_no_banner_exits_zero(self):
        """--no-banner must exit with code 0 on a valid dry-run."""
        result = _run_init("--no-banner", "--dry-run")
        assert result.exit_code == 0, result.output

    def test_no_banner_suppresses_banner(self):
        """--no-banner must suppress the ASCII art banner text."""
        result = _run_init("--no-banner", "--dry-run")
        assert BANNER_MARKER not in result.output, (
            f"Expected banner suppressed but found '{BANNER_MARKER}' in:\n{result.output}"
        )

    def test_without_no_banner_shows_banner(self):
        """Without --no-banner, the banner must appear in init output."""
        result = _run_init("--dry-run")
        assert BANNER_MARKER in result.output, (
            f"Expected banner present in output but not found:\n{result.output}"
        )

    def test_no_banner_with_dry_run(self):
        """--no-banner --dry-run must show preview but no banner."""
        result = _run_init("--no-banner", "--dry-run")
        assert result.exit_code == 0, result.output
        assert BANNER_MARKER not in result.output
        assert "dry run" in result.output.lower() or "no files will be written" in result.output.lower(), (
            f"Expected dry-run preview panel:\n{result.output}"
        )

    def test_no_banner_with_here_flag(self):
        """--no-banner --here must work and suppress banner."""
        result = runner.invoke(app, [
            "init", "--here",
            "--no-banner",
            "--dry-run",
            "--ai", "copilot",
            "--script", "sh",
            "--no-git",
            "--ignore-agent-tools",
            "--force",
        ], catch_exceptions=False)
        assert result.exit_code == 0, result.output
        assert BANNER_MARKER not in result.output

    def test_no_banner_does_not_affect_functionality(self):
        """--no-banner must not prevent file creation in normal init."""
        with patch("specify_cli.download_and_extract_template") as mock_dl:
            mock_dl.return_value = None
            with tempfile.TemporaryDirectory() as tmpdir:
                project_dir = Path(tmpdir) / "my-project"
                result = runner.invoke(app, [
                    "init", str(project_dir),
                    "--no-banner",
                    "--ai", "copilot",
                    "--script", "sh",
                    "--no-git",
                    "--ignore-agent-tools",
                ])
        # download was called (functionality not skipped)
        mock_dl.assert_called_once()

    def test_no_banner_invalid_agent_still_errors(self):
        """--no-banner with invalid --ai must still exit with error."""
        result = runner.invoke(app, [
            "init", "test-project",
            "--no-banner",
            "--ai", "notanagent",
        ])
        assert result.exit_code == 1
        assert "Invalid AI assistant" in result.output
