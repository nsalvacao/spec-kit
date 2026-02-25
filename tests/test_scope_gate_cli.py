"""CLI tests for `specify scope-gate` decision flow."""

import json

from typer.testing import CliRunner

from specify_cli import app


runner = CliRunner()


def test_scope_gate_follow_path_emits_handoff_ready_state():
    result = runner.invoke(
        app,
        [
            "scope-gate",
            "--decision",
            "follow",
            "--description",
            "Add status filter to customer listing.",
        ],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["decision_option"] == "follow"
    assert payload["state_trace"][-1] == "handoff_ready"
    assert payload["scope_gate"]["override_flag"] is False


def test_scope_gate_override_requires_rationale():
    result = runner.invoke(
        app,
        [
            "scope-gate",
            "--decision",
            "override",
            "--description",
            "Create onboarding capability with several internal integrations.",
            "--timeline-weeks",
            "8",
            "--work-items",
            "3",
            "--dependencies",
            "3",
            "--integrations",
            "2",
            "--domains",
            "2",
            "--teams",
            "2",
            "--risk-level",
            "medium",
            "--override-mode",
            "feature",
            "--risk-acknowledged",
        ],
    )

    assert result.exit_code == 1
    assert "override_rationale is required" in result.output


def test_scope_gate_override_requires_risk_acknowledgment_for_epic_or_program():
    result = runner.invoke(
        app,
        [
            "scope-gate",
            "--decision",
            "override",
            "--description",
            "Create onboarding capability with several internal integrations.",
            "--timeline-weeks",
            "8",
            "--work-items",
            "3",
            "--dependencies",
            "3",
            "--integrations",
            "2",
            "--domains",
            "2",
            "--teams",
            "2",
            "--risk-level",
            "medium",
            "--override-mode",
            "feature",
            "--override-rationale",
            "Need emergency narrow patch first.",
        ],
    )

    assert result.exit_code == 1
    assert "risk_acknowledged is required" in result.output


def test_scope_gate_valid_override_emits_override_flag():
    result = runner.invoke(
        app,
        [
            "scope-gate",
            "--decision",
            "override",
            "--description",
            "Create onboarding capability with several internal integrations.",
            "--timeline-weeks",
            "8",
            "--work-items",
            "3",
            "--dependencies",
            "3",
            "--integrations",
            "2",
            "--domains",
            "2",
            "--teams",
            "2",
            "--risk-level",
            "medium",
            "--override-mode",
            "feature",
            "--override-rationale",
            "Need emergency narrow patch first.",
            "--risk-acknowledged",
            "--compact",
        ],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["decision_option"] == "override"
    assert payload["risk_acknowledged"] is True
    assert payload["scope_gate"]["override_flag"] is True
    assert payload["scope_gate"]["user_choice"] == "feature"


def test_scope_gate_json_input_requires_non_empty_description(tmp_path):
    input_file = tmp_path / "scope-input.json"
    input_file.write_text(
        json.dumps(
            {
                "description": "   ",
                "estimated_timeline_weeks": 4,
            }
        ),
        encoding="utf-8",
    )

    result = runner.invoke(
        app,
        [
            "scope-gate",
            "--decision",
            "follow",
            "--input-json",
            str(input_file),
            "--project-root",
            str(tmp_path),
        ],
    )

    assert result.exit_code == 1
    assert "A non-empty description is required" in result.output


def test_scope_gate_rejects_input_json_outside_project_root(tmp_path):
    project_root = tmp_path / "project"
    project_root.mkdir()
    outside_file = tmp_path / "outside-input.json"
    outside_file.write_text(json.dumps({"description": "Scope input"}), encoding="utf-8")

    result = runner.invoke(
        app,
        [
            "scope-gate",
            "--decision",
            "follow",
            "--input-json",
            str(outside_file),
            "--project-root",
            str(project_root),
        ],
    )

    assert result.exit_code == 1
    assert "must be within project root" in result.output


def test_scope_gate_rejects_output_json_outside_project_root(tmp_path):
    project_root = tmp_path / "project"
    project_root.mkdir()
    input_file = project_root / "scope-input.json"
    input_file.write_text(json.dumps({"description": "Scope input"}), encoding="utf-8")
    outside_output = tmp_path / "outside-output.json"

    result = runner.invoke(
        app,
        [
            "scope-gate",
            "--decision",
            "follow",
            "--input-json",
            str(input_file),
            "--output-json",
            str(outside_output),
            "--project-root",
            str(project_root),
        ],
    )

    assert result.exit_code == 1
    assert "must be within project root" in result.output
