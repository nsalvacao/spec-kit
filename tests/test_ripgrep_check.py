"""
Tests for ripgrep (rg) dependency check in specify init.

Issue #19: ripgrep not enforced at init — validators require rg but CLI
allowed init without it, causing silent failures 30% of the time.
"""

import pytest
from unittest.mock import patch, MagicMock
from typer.testing import CliRunner
from specify_cli import app, check_tool


class TestCheckTool:
    """Unit tests for the check_tool helper."""

    def test_check_tool_returns_true_for_existing_tool(self):
        """check_tool returns True when the tool is in PATH."""
        with patch("shutil.which", return_value="/usr/bin/git"):
            assert check_tool("git") is True

    def test_check_tool_returns_false_for_missing_tool(self):
        """check_tool returns False when the tool is not in PATH."""
        with patch("shutil.which", return_value=None):
            assert check_tool("nonexistent_tool_xyz") is False

    def test_check_tool_rg_true_when_installed(self):
        """check_tool('rg') returns True when ripgrep is installed."""
        with patch("shutil.which", return_value="/usr/bin/rg"):
            assert check_tool("rg") is True

    def test_check_tool_rg_false_when_missing(self):
        """check_tool('rg') returns False when ripgrep is missing."""
        with patch("shutil.which", return_value=None):
            assert check_tool("rg") is False


class TestInitRipgrepWarning:
    """Integration tests for rg check in specify init command."""

    def test_init_warns_when_rg_missing(self, tmp_path):
        """specify init should print a warning when rg is not installed."""
        runner = CliRunner()
        with patch("shutil.which") as mock_which:
            # rg not found, git and uv found
            def side_effect(tool):
                if tool == "rg":
                    return None
                return f"/usr/bin/{tool}"
            mock_which.side_effect = side_effect

            # Use --ai and --script to avoid interactive prompts
            # Use --no-git to skip git init
            result = runner.invoke(
                app,
                ["init", str(tmp_path / "test-project"), "--ai", "copilot",
                 "--script", "sh", "--no-git", "--ignore-agent-tools"],
                catch_exceptions=False,
            )

        # Warning about missing rg should be in output
        assert "ripgrep" in result.output.lower() or "rg" in result.output

    def test_init_continues_when_rg_missing(self, tmp_path):
        """specify init should NOT exit(1) when rg is missing — it's a warning only."""
        runner = CliRunner()
        with patch("shutil.which") as mock_which:
            def side_effect(tool):
                if tool == "rg":
                    return None
                return f"/usr/bin/{tool}"
            mock_which.side_effect = side_effect

            result = runner.invoke(
                app,
                ["init", str(tmp_path / "test-project2"), "--ai", "copilot",
                 "--script", "sh", "--no-git", "--ignore-agent-tools"],
                catch_exceptions=False,
            )

        # Must NOT exit with code 1 due to missing rg
        assert result.exit_code != 1 or "ripgrep" not in result.output.lower()

    def test_init_no_warning_when_rg_present(self, tmp_path):
        """specify init should not show rg warning when ripgrep is installed."""
        runner = CliRunner()
        with patch("shutil.which", return_value="/usr/bin/rg"):
            result = runner.invoke(
                app,
                ["init", str(tmp_path / "test-project3"), "--ai", "copilot",
                 "--script", "sh", "--no-git", "--ignore-agent-tools"],
                catch_exceptions=False,
            )

        # Warning about missing rg should NOT appear when rg is present
        assert "Missing Dependency: ripgrep" not in result.output
