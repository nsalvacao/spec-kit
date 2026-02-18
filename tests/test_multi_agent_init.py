"""Tests for multi-agent --ai flag: --ai copilot,claude support (issue #25)."""
import pytest
from typer.testing import CliRunner
from unittest.mock import patch, MagicMock
from specify_cli import app, AGENT_CONFIG

runner = CliRunner()

# Minimal set of patches needed to avoid network I/O in init()
BASE_PATCHES = [
    ("specify_cli.download_and_extract_template",),
    ("specify_cli.ensure_executable_scripts",),
    ("specify_cli.ensure_constitution_from_template",),
    ("specify_cli.ensure_gitignore_security",),
]


def _run_init(*extra_args):
    """Helper: run init with no-git, ignore-agent-tools, and sh script."""
    return runner.invoke(app, [
        "init", "test-project",
        "--script", "sh",
        "--no-git",
        "--ignore-agent-tools",
        *extra_args,
    ])


class TestMultiAgentParsing:
    """Unit tests: comma-separated --ai parsing and validation."""

    def test_single_agent_still_works(self):
        """--ai copilot (single) must still work."""
        with patch("specify_cli.download_and_extract_template") as mock_dl, \
             patch("specify_cli.ensure_executable_scripts"), \
             patch("specify_cli.ensure_constitution_from_template"), \
             patch("specify_cli.ensure_gitignore_security", return_value="updated"):
            mock_dl.return_value = MagicMock()
            result = _run_init("--ai", "copilot")
        assert "Invalid AI assistant" not in (result.output or "")

    def test_multi_agent_invalid_key_rejected(self):
        """--ai copilot,notreal must exit with error."""
        result = _run_init("--ai", "copilot,notreal")
        assert result.exit_code == 1
        assert "Invalid AI assistant" in result.output
        assert "notreal" in result.output

    def test_multi_agent_all_invalid_rejected(self):
        """--ai foo,bar must exit with error listing both."""
        result = _run_init("--ai", "foo,bar")
        assert result.exit_code == 1
        assert "Invalid AI assistant" in result.output

    def test_valid_multi_agent_accepted(self):
        """--ai copilot,claude should pass validation (both in AGENT_CONFIG)."""
        with patch("specify_cli.download_and_extract_template") as mock_dl, \
             patch("specify_cli.ensure_executable_scripts"), \
             patch("specify_cli.ensure_constitution_from_template"), \
             patch("specify_cli.ensure_gitignore_security", return_value="updated"):
            mock_dl.return_value = MagicMock()
            result = _run_init("--ai", "copilot,claude")
        assert "Invalid AI assistant" not in (result.output or "")

    def test_whitespace_trimmed_in_agent_list(self):
        """--ai 'notakey, alsonotakey' (with space) should trim and validate."""
        result = _run_init("--ai", "notakey, alsonotakey")
        assert result.exit_code == 1
        assert "Invalid AI assistant" in result.output

    def test_all_known_agents_are_valid(self):
        """Every key in AGENT_CONFIG must be accepted without 'Invalid' error."""
        for key in AGENT_CONFIG:
            with patch("specify_cli.download_and_extract_template") as mock_dl, \
                 patch("specify_cli.ensure_executable_scripts"), \
                 patch("specify_cli.ensure_constitution_from_template"), \
                 patch("specify_cli.ensure_gitignore_security", return_value="updated"):
                mock_dl.return_value = MagicMock()
                result = runner.invoke(app, [
                    "init", f"test-{key}",
                    "--ai", key,
                    "--script", "sh",
                    "--no-git",
                    "--ignore-agent-tools",
                ])
            assert "Invalid AI assistant" not in (result.output or ""), \
                f"Agent '{key}' was incorrectly rejected"


class TestMultiAgentDownload:
    """Tests that extra agents trigger additional download calls."""

    def test_two_agents_triggers_two_downloads(self):
        """--ai copilot,claude should call download_and_extract_template twice."""
        with patch("specify_cli.download_and_extract_template") as mock_dl, \
             patch("specify_cli.ensure_executable_scripts"), \
             patch("specify_cli.ensure_constitution_from_template"), \
             patch("specify_cli.ensure_gitignore_security", return_value="updated"):
            mock_dl.return_value = MagicMock()
            _run_init("--ai", "copilot,claude")
        assert mock_dl.call_count == 2
        first_call_agent = mock_dl.call_args_list[0][0][1]
        second_call_agent = mock_dl.call_args_list[1][0][1]
        assert first_call_agent == "copilot"
        assert second_call_agent == "claude"

    def test_three_agents_triggers_three_downloads(self):
        """--ai copilot,claude,gemini should call download three times."""
        with patch("specify_cli.download_and_extract_template") as mock_dl, \
             patch("specify_cli.ensure_executable_scripts"), \
             patch("specify_cli.ensure_constitution_from_template"), \
             patch("specify_cli.ensure_gitignore_security", return_value="updated"):
            mock_dl.return_value = MagicMock()
            _run_init("--ai", "copilot,claude,gemini")
        assert mock_dl.call_count == 3

    def test_extra_agent_uses_is_current_dir_true(self):
        """Extra agent download must always use is_current_dir=True (overlay mode)."""
        with patch("specify_cli.download_and_extract_template") as mock_dl, \
             patch("specify_cli.ensure_executable_scripts"), \
             patch("specify_cli.ensure_constitution_from_template"), \
             patch("specify_cli.ensure_gitignore_security", return_value="updated"):
            mock_dl.return_value = MagicMock()
            _run_init("--ai", "copilot,claude")
        second_call_kwargs = mock_dl.call_args_list[1][1]
        assert second_call_kwargs.get("is_current_dir") is True

    def test_extra_agent_failure_does_not_abort_init(self):
        """If extra-agent download fails, init should still complete."""
        call_count = 0

        def side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 2:
                raise RuntimeError("Network error for extra agent")

        with patch("specify_cli.download_and_extract_template", side_effect=side_effect), \
             patch("specify_cli.ensure_executable_scripts"), \
             patch("specify_cli.ensure_constitution_from_template"), \
             patch("specify_cli.ensure_gitignore_security", return_value="updated"):
            result = _run_init("--ai", "copilot,claude")
        # Primary agent succeeded; extra failed but init should not crash
        assert result.exit_code == 0
