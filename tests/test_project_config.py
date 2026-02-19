"""Tests for project-level Spec-Kit configuration loading."""

from pathlib import Path

import pytest

from specify_cli.project_config import (
    DEFAULT_PROJECT_CONFIG,
    load_project_config,
    parse_env_overrides,
)


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def test_load_project_config_returns_defaults_when_no_files(tmp_path: Path):
    config = load_project_config(project_root=tmp_path)
    assert config["schema_version"] == DEFAULT_PROJECT_CONFIG["schema_version"]
    assert config["scope_detection"] == {}


def test_project_and_local_config_merge_with_precedence(tmp_path: Path):
    _write(
        tmp_path / ".specify" / "spec-kit.yml",
        """
schema_version: 1
scope_detection:
  work_items_multiplier: 4
  domain_multiplier: 8
""".strip(),
    )
    _write(
        tmp_path / ".specify" / "spec-kit.local.yml",
        """
scope_detection:
  work_items_multiplier: 2
  cross_team_multiplier: 1
""".strip(),
    )

    config = load_project_config(project_root=tmp_path)
    assert config["scope_detection"]["work_items_multiplier"] == 2
    assert config["scope_detection"]["domain_multiplier"] == 8
    assert config["scope_detection"]["cross_team_multiplier"] == 1


def test_env_overrides_are_applied_last(tmp_path: Path):
    _write(
        tmp_path / ".specify" / "spec-kit.yml",
        """
scope_detection:
  work_items_multiplier: 4
  keyword_cap: 8
""".strip(),
    )
    env = {
        "SPECIFY_CONFIG__SCOPE_DETECTION__WORK_ITEMS_MULTIPLIER": "3",
        "SPECIFY_CONFIG__SCOPE_DETECTION__COMPLEXITY_KEYWORDS": '["platform","migration","security"]',
    }

    config = load_project_config(project_root=tmp_path, env=env)
    assert config["scope_detection"]["work_items_multiplier"] == 3
    assert config["scope_detection"]["keyword_cap"] == 8
    assert config["scope_detection"]["complexity_keywords"] == ["platform", "migration", "security"]


def test_parse_env_overrides_handles_nested_paths():
    overrides = parse_env_overrides(
        {
            "SPECIFY_CONFIG__SCOPE_DETECTION__FEATURE_MAX_SCORE": "30",
            "SPECIFY_CONFIG__SCOPE_DETECTION__RISK_WEIGHTS__HIGH": "10",
        }
    )
    assert overrides["scope_detection"]["feature_max_score"] == 30
    assert overrides["scope_detection"]["risk_weights"]["high"] == 10


def test_invalid_yaml_raises_value_error(tmp_path: Path):
    _write(tmp_path / ".specify" / "spec-kit.yml", "{ invalid: [yaml }")
    with pytest.raises(ValueError, match="Invalid YAML"):
        load_project_config(project_root=tmp_path)


def test_non_mapping_yaml_raises_value_error(tmp_path: Path):
    _write(tmp_path / ".specify" / "spec-kit.yml", "- just\n- a\n- list\n")
    with pytest.raises(ValueError, match="must contain a YAML mapping"):
        load_project_config(project_root=tmp_path)
