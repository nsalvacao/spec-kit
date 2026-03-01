"""Tests for native productivity start flow (issue #200, A1)."""

from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from specify_cli import app
from specify_cli.productivity import prepare_productivity_scaffold, run_productivity_start


runner = CliRunner()


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_prepare_productivity_scaffold_creates_missing_artifacts(tmp_path: Path) -> None:
    result = prepare_productivity_scaffold(tmp_path, host="127.0.0.1", port=8001)

    assert result.bootstrap_required is True
    assert (tmp_path / "TASKS.md").exists()
    assert (tmp_path / "CLAUDE.md").exists()
    assert (tmp_path / "memory").is_dir()
    assert (tmp_path / "memory" / "bootstrap.md").exists()
    assert (tmp_path / ".cockpit.json").exists()
    assert result.tasks_path_for_cockpit == "TASKS.md"

    config = _read_json(tmp_path / ".cockpit.json")
    assert config["service"]["host"] == "127.0.0.1"
    assert config["service"]["port"] == 8001
    assert config["paths"]["tasks"] == "TASKS.md"


def test_prepare_productivity_scaffold_is_idempotent(tmp_path: Path) -> None:
    first = prepare_productivity_scaffold(tmp_path, host="127.0.0.1", port=8001)
    assert first.created

    claude = tmp_path / "CLAUDE.md"
    claude.write_text("# custom memory\n", encoding="utf-8")

    second = prepare_productivity_scaffold(tmp_path, host="127.0.0.1", port=8001)
    assert "CLAUDE.md" in second.existing
    assert claude.read_text(encoding="utf-8") == "# custom memory\n"


def test_prepare_productivity_scaffold_prefers_canonical_feature_tasks(
    tmp_path: Path, monkeypatch
) -> None:
    feature_id = "001-user-auth"
    specs_tasks = tmp_path / "specs" / feature_id / "tasks.md"
    specs_tasks.parent.mkdir(parents=True)
    specs_tasks.write_text("# feature tasks\n", encoding="utf-8")
    monkeypatch.setenv("SPECIFY_FEATURE", feature_id)

    result = prepare_productivity_scaffold(tmp_path, host="127.0.0.1", port=8001)

    assert result.tasks_path_for_cockpit == f"specs/{feature_id}/tasks.md"
    config = _read_json(tmp_path / ".cockpit.json")
    assert config["paths"]["tasks"] == f"specs/{feature_id}/tasks.md"
    assert (tmp_path / "TASKS.md").exists()  # compatibility scaffold still created


def test_run_productivity_start_supports_scaffold_only_mode(tmp_path: Path) -> None:
    outcome = run_productivity_start(
        project_root=tmp_path,
        host="127.0.0.1",
        preferred_port=8001,
        start_server=False,
        open_browser=False,
    )

    assert outcome.ok is True
    assert outcome.server_started is False
    assert outcome.server_reused is False
    assert outcome.browser_opened is False
    assert "Browser opening skipped by option. Cockpit URL:" in "\n".join(outcome.notes)


def test_productivity_start_cli_compact_output(tmp_path: Path) -> None:
    result = runner.invoke(
        app,
        [
            "productivity",
            "start",
            "--project-root",
            str(tmp_path),
            "--no-server",
            "--no-browser",
            "--compact",
        ],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["ok"] is True
    assert payload["scaffold"]["bootstrap_required"] is True
    assert payload["scaffold"]["tasks_path_for_cockpit"]
