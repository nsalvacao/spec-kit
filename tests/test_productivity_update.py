"""Tests for native productivity update flow (issue #201, A2)."""

from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from specify_cli import app
from specify_cli.productivity import run_productivity_update


runner = CliRunner()


def _seed_productivity_state(tmp_path: Path) -> None:
    (tmp_path / "TASKS.md").write_text(
        """# Tasks

## Active
- [ ] **Existing Task** - for Alex due 2024-01-01 since 2024-01-01
- [ ] **Phoenix follow-up** - sync blockers
- [ ] **Share brief** - https://example.com/brief

## Waiting On
- [ ] **Wait legal review** - since 2024-02-01

## Someday

## Done
""",
        encoding="utf-8",
    )
    (tmp_path / "CLAUDE.md").write_text(
        """# Memory

## Terms
| Term | Meaning |
|------|---------|
| API | Application Programming Interface |
""",
        encoding="utf-8",
    )
    memory_dir = tmp_path / "memory"
    memory_dir.mkdir(parents=True)
    (memory_dir / "glossary.md").write_text("# Glossary\n\n## Acronyms\n", encoding="utf-8")


def test_run_productivity_update_requires_scaffold(tmp_path: Path) -> None:
    outcome = run_productivity_update(project_root=tmp_path, sync_github=False)

    assert outcome.ok is False
    assert outcome.error
    assert "Run 'specify productivity start' first" in outcome.error


def test_run_productivity_update_detects_sync_stale_and_memory_gaps(tmp_path: Path) -> None:
    _seed_productivity_state(tmp_path)

    outcome = run_productivity_update(
        project_root=tmp_path,
        sync_github=False,
        external_tasks=["Existing Task", "Review QBR with Maya"],
        stale_days=30,
    )

    assert outcome.ok is True
    additions = outcome.task_sync["additions"]
    duplicates = outcome.task_sync["duplicates"]
    assert any(item["title"] == "Review QBR with Maya" for item in additions)
    assert any(item["external_title"] == "Existing Task" for item in duplicates)

    stale_titles = {item["title"] for item in outcome.stale_findings}
    assert "Existing Task" in stale_titles
    assert any("missing_context" in item["reasons"] for item in outcome.stale_findings if item["title"] == "Phoenix follow-up")

    memory_entities = {item["entity"] for item in outcome.memory_gaps}
    assert "QBR" in memory_entities
    assert any(item["kind"] == "link" for item in outcome.memory_enrichment)


def test_run_productivity_update_apply_yes_writes_tasks_and_memory(tmp_path: Path) -> None:
    _seed_productivity_state(tmp_path)

    outcome = run_productivity_update(
        project_root=tmp_path,
        sync_github=False,
        external_tasks=["Design review with Maya"],
        apply_changes=True,
        auto_confirm=True,
    )

    assert outcome.ok is True
    assert "Design review with Maya" in outcome.applied["tasks"]
    assert outcome.applied["memory"]  # at least one unknown entity placeholder

    tasks_content = (tmp_path / "TASKS.md").read_text(encoding="utf-8")
    assert "Design review with Maya" in tasks_content
    glossary_content = (tmp_path / "memory" / "glossary.md").read_text(encoding="utf-8")
    assert "## Intake Candidates" in glossary_content


def test_run_productivity_update_comprehensive_produces_candidates(tmp_path: Path) -> None:
    _seed_productivity_state(tmp_path)
    (tmp_path / "docs").mkdir(parents=True)
    (tmp_path / "docs" / "notes.md").write_text(
        """# Notes

TODO: prepare release checklist for Starlight handoff
ACTION: review RFD with Platform team
RFD discussion continued in weekly notes.
""",
        encoding="utf-8",
    )

    outcome = run_productivity_update(
        project_root=tmp_path,
        sync_github=False,
        comprehensive=True,
    )

    assert outcome.ok is True
    assert outcome.comprehensive is not None
    assert outcome.comprehensive["candidate_tasks"]
    memory_candidates = {item["entity"] for item in outcome.comprehensive["candidate_memory"]}
    assert "RFD" in memory_candidates


def test_productivity_update_cli_compact_output(tmp_path: Path) -> None:
    _seed_productivity_state(tmp_path)
    result = runner.invoke(
        app,
        [
            "productivity",
            "update",
            "--project-root",
            str(tmp_path),
            "--compact",
            "--no-github-sync",
            "--external-task",
            "Prepare retro notes",
        ],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["ok"] is True
    assert payload["mode"] == "default"
    assert any(item["title"] == "Prepare retro notes" for item in payload["task_sync"]["additions"])

