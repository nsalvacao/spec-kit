"""Tests for `specify scope-detect` command integration."""

import json

from typer.testing import CliRunner

from specify_cli import app


runner = CliRunner()


def test_scope_detect_with_inline_options_emits_combined_payload():
    result = runner.invoke(
        app,
        [
            "scope-detect",
            "--description",
            "Add status filter to customer listing.",
            "--timeline-weeks",
            "2",
            "--work-items",
            "1",
            "--dependencies",
            "0",
            "--integrations",
            "0",
            "--domains",
            "1",
            "--teams",
            "1",
            "--risk-level",
            "low",
        ],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert "scope_detection" in payload
    assert "scope_gate" in payload
    assert payload["scope_detection"]["mode_recommendation"] in {"feature", "epic", "program"}
    assert payload["scope_gate"]["mode_recommendation"] == payload["scope_detection"]["mode_recommendation"]
    assert payload["scope_gate"]["user_choice"] == payload["scope_gate"]["mode_recommendation"]


def test_scope_detect_accepts_json_input_and_writes_output_file(tmp_path):
    input_file = tmp_path / "scope-input.json"
    output_file = tmp_path / "scope-output.json"
    input_file.write_text(
        json.dumps(
            {
                "description": "Platform migration with cross-team dependencies.",
                "estimated_timeline_weeks": "10",
                "expected_work_items": "4",
                "dependency_count": "4",
                "integration_surface_count": "3",
                "domain_count": "2",
                "cross_team_count": "2",
                "risk_level": "high",
                "requires_compliance_review": "true",
                "requires_migration": "true",
            }
        ),
        encoding="utf-8",
    )

    result = runner.invoke(
        app,
        [
            "scope-detect",
            "--input-json",
            str(input_file),
            "--output-json",
            str(output_file),
            "--project-root",
            str(tmp_path),
            "--compact",
        ],
    )

    assert result.exit_code == 0, result.output
    stdout_payload = json.loads(result.output)
    file_payload = json.loads(output_file.read_text(encoding="utf-8"))
    assert stdout_payload == file_payload
    assert file_payload["scope_gate"]["override_flag"] is False
    assert file_payload["scope_gate"]["next_action"]


def test_scope_detect_requires_description_without_input_json():
    result = runner.invoke(app, ["scope-detect"])

    assert result.exit_code == 1
    assert "description is required when --input-json is not provided" in result.output


def test_scope_detect_rejects_input_json_outside_project_root(tmp_path):
    project_root = tmp_path / "project"
    project_root.mkdir()
    outside_file = tmp_path / "scope-input.json"
    outside_file.write_text(json.dumps({"description": "Scope input"}), encoding="utf-8")

    result = runner.invoke(
        app,
        [
            "scope-detect",
            "--input-json",
            str(outside_file),
            "--project-root",
            str(project_root),
        ],
    )

    assert result.exit_code == 1
    assert "must be within project root" in result.output


def test_scope_detect_rejects_output_json_outside_project_root(tmp_path):
    project_root = tmp_path / "project"
    project_root.mkdir()
    input_file = project_root / "scope-input.json"
    input_file.write_text(json.dumps({"description": "Scope input"}), encoding="utf-8")
    outside_output = tmp_path / "scope-output.json"

    result = runner.invoke(
        app,
        [
            "scope-detect",
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
