"""Tests for productivity cockpit config schema and safety guards (issue #203)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from specify_cli.productivity_config import (
    DEFAULT_MAX_COCKPIT_CONFIG_FILE_BYTES,
    ProductivityUpdateConfig,
    cockpit_config_from_mapping,
    load_cockpit_config,
    load_productivity_update_config,
    productivity_update_config_from_mapping,
    resolve_project_relative_path,
)


def test_cockpit_config_from_mapping_accepts_legacy_ai_cli_empty() -> None:
    payload = cockpit_config_from_mapping(
        {
            "name": "Project Cockpit",
            "version": "2.0.0",
            "service": {"host": "127.0.0.1", "port": 8001},
            "paths": {"tasks": "TASKS.md", "memory": "memory", "output": "output"},
            "pulse_rules": {"essential_files": ["README.md"], "min_folders": []},
            "ai": {"mode": "cli", "cli": "", "args": []},
        }
    )

    assert payload.schema_version == 1
    assert payload.ai.mode == "cli"
    assert payload.ai.cli == ""


def test_cockpit_config_from_mapping_rejects_unknown_keys() -> None:
    with pytest.raises(ValueError, match="Unknown cockpit config keys"):
        cockpit_config_from_mapping({"unknown": 1})


def test_cockpit_config_from_mapping_rejects_invalid_ai_mode() -> None:
    with pytest.raises(ValueError, match="ai.mode"):
        cockpit_config_from_mapping({"ai": {"mode": "invalid"}})


def test_resolve_project_relative_path_rejects_absolute_path(tmp_path: Path) -> None:
    absolute = str((tmp_path / "TASKS.md").resolve())
    with pytest.raises(ValueError, match="must be a project-relative path"):
        resolve_project_relative_path(tmp_path, absolute, field_name="paths.tasks")


def test_resolve_project_relative_path_rejects_path_traversal(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="path traversal"):
        resolve_project_relative_path(tmp_path, "../outside.md", field_name="paths.tasks")


def test_resolve_project_relative_path_rejects_symlink_escape(tmp_path: Path) -> None:
    outside = tmp_path.parent / f"{tmp_path.name}-outside"
    outside.mkdir(parents=True, exist_ok=True)
    (outside / "tasks.md").write_text("# outside\n", encoding="utf-8")

    linked = tmp_path / "linked"
    try:
        linked.symlink_to(outside, target_is_directory=True)
    except OSError:
        pytest.skip("Symlink creation is not available in this environment.")

    with pytest.raises(ValueError, match="outside project root"):
        resolve_project_relative_path(tmp_path, "linked/tasks.md", field_name="paths.tasks")


def test_load_cockpit_config_raises_on_invalid_json(tmp_path: Path) -> None:
    (tmp_path / ".cockpit.json").write_text("{invalid", encoding="utf-8")

    with pytest.raises(ValueError, match="Could not parse .cockpit.json"):
        load_cockpit_config(tmp_path)


def test_load_cockpit_config_rejects_oversized_file(tmp_path: Path) -> None:
    (tmp_path / ".cockpit.json").write_bytes(b"x" * (DEFAULT_MAX_COCKPIT_CONFIG_FILE_BYTES + 1))

    with pytest.raises(ValueError, match="exceeds size limit"):
        load_cockpit_config(tmp_path)


def test_load_cockpit_config_rejects_non_utf8(tmp_path: Path) -> None:
    (tmp_path / ".cockpit.json").write_bytes(b"\xff\xfe\x00")

    with pytest.raises(ValueError, match="expected UTF-8"):
        load_cockpit_config(tmp_path)


def test_productivity_update_config_from_mapping_rejects_unknown_keys() -> None:
    with pytest.raises(ValueError, match="Unknown productivity_update config keys"):
        productivity_update_config_from_mapping({"unknown": 1})


def test_load_productivity_update_config_reads_project_overrides(tmp_path: Path) -> None:
    spec_kit_config = tmp_path / ".specify" / "spec-kit.yml"
    spec_kit_config.parent.mkdir(parents=True, exist_ok=True)
    spec_kit_config.write_text(
        """
schema_version: 1
productivity_update:
  fuzzy_title_match_threshold: 0.9
  default_stale_age_days: 21
  max_comprehensive_scan_files: 12
  max_comprehensive_scan_file_bytes: 64000
""".strip(),
        encoding="utf-8",
    )

    loaded = load_productivity_update_config(project_root=tmp_path)
    assert isinstance(loaded, ProductivityUpdateConfig)
    assert loaded.fuzzy_title_match_threshold == 0.9
    assert loaded.default_stale_age_days == 21
    assert loaded.max_comprehensive_scan_files == 12
    assert loaded.max_comprehensive_scan_file_bytes == 64000


def test_load_cockpit_config_accepts_legacy_without_schema_version(tmp_path: Path) -> None:
    payload = {
        "name": "Legacy Cockpit",
        "version": "2.0.0",
        "service": {"host": "127.0.0.1", "port": 8001},
        "paths": {"tasks": "TASKS.md", "memory": "memory", "output": "output"},
        "pulse_rules": {"essential_files": ["README.md"], "min_folders": []},
        "ai": {"mode": "cli", "cli": "", "args": []},
    }
    (tmp_path / ".cockpit.json").write_text(json.dumps(payload), encoding="utf-8")

    loaded = load_cockpit_config(tmp_path)
    assert loaded.schema_version == 1
    assert loaded.ai.cli == ""
