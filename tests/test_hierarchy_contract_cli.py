"""CLI tests for hierarchy metadata contract normalization."""

import json

from typer.testing import CliRunner

from specify_cli import app


runner = CliRunner()


def test_hierarchy_contract_command_normalizes_feature_payload(tmp_path):
    input_file = tmp_path / "hierarchy.json"
    input_file.write_text(
        json.dumps(
            {
                "mode": "feature",
                "features": [
                    {
                        "id": "099-Reporting-Export",
                        "title": "Reporting export",
                        "status": "draft",
                        "owner": "team-analytics",
                        "artifacts": {
                            "spec": "specs/099-reporting-export/spec.md",
                            "plan": "specs/099-reporting-export/plan.md",
                            "tasks": "specs/099-reporting-export/tasks.md",
                        },
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    result = runner.invoke(
        app,
        [
            "hierarchy-contract",
            "--input-json",
            str(input_file),
            "--compact",
        ],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["mode"] == "feature"
    assert payload["features"][0]["id"] == "099-reporting-export"


def test_hierarchy_contract_command_rejects_invalid_payload(tmp_path):
    input_file = tmp_path / "invalid-hierarchy.json"
    input_file.write_text(json.dumps({"mode": "feature", "features": []}), encoding="utf-8")

    result = runner.invoke(app, ["hierarchy-contract", "--input-json", str(input_file)])

    assert result.exit_code == 1
    assert "at least one feature" in result.output


def test_hierarchy_contract_command_handles_output_path_directory_error(tmp_path):
    input_file = tmp_path / "hierarchy.json"
    input_file.write_text(
        json.dumps(
            {
                "mode": "feature",
                "features": [
                    {
                        "id": "099-reporting-export",
                        "title": "Reporting export",
                        "status": "draft",
                        "owner": "team-analytics",
                        "artifacts": {
                            "spec": "specs/099-reporting-export/spec.md",
                            "plan": "specs/099-reporting-export/plan.md",
                            "tasks": "specs/099-reporting-export/tasks.md",
                        },
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    output_dir = tmp_path / "existing-dir"
    output_dir.mkdir()

    result = runner.invoke(
        app,
        [
            "hierarchy-contract",
            "--input-json",
            str(input_file),
            "--output-json",
            str(output_dir),
        ],
    )

    assert result.exit_code == 1
    assert "Error:" in result.output
