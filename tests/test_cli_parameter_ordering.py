"""Tests for robust CLI option-value parsing around --ai."""

from typer.testing import CliRunner

from specify_cli import app


runner = CliRunner()


def test_ai_flag_missing_value_reports_helpful_error():
    """`--ai --here` should fail with a targeted message, not generic init errors."""
    result = runner.invoke(app, ["init", "--ai", "--here", "--no-banner"])

    assert result.exit_code == 1
    assert "Invalid value for --ai" in result.output
    assert "--here" in result.output
    assert "Did you forget to provide a value for --ai?" in result.output


def test_ai_flag_missing_value_lists_available_agents():
    """Error should point users to valid agent keys for fast recovery."""
    result = runner.invoke(app, ["init", "--ai", "--force", "--no-banner"])

    assert result.exit_code == 1
    assert "Available agents:" in result.output
    assert "claude" in result.output
    assert "copilot" in result.output


def test_ai_flag_short_option_like_value_reports_helpful_error():
    """`--ai -x` should also be treated as an invalid value for --ai."""
    result = runner.invoke(app, ["init", "--ai", "-x", "--no-banner"])

    assert result.exit_code == 1
    assert "Invalid value for --ai" in result.output
    assert "-x" in result.output
