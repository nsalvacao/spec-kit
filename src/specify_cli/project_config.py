"""Project-level configuration loader for Spec-Kit runtime settings.

Configuration precedence (lowest -> highest):
1. Built-in defaults
2. `.specify/spec-kit.yml` (project-shared, committed)
3. `.specify/spec-kit.local.yml` (machine-local, should be gitignored)
4. `SPECIFY_CONFIG__...` environment overrides
"""

from __future__ import annotations

from copy import deepcopy
import os
from pathlib import Path
from typing import Any, Mapping

import yaml


PROJECT_CONFIG_REL_PATH = Path(".specify/spec-kit.yml")
PROJECT_LOCAL_CONFIG_REL_PATH = Path(".specify/spec-kit.local.yml")
ENV_CONFIG_PREFIX = "SPECIFY_CONFIG__"

DEFAULT_PROJECT_CONFIG: dict[str, Any] = {
    "schema_version": 1,
    "scope_detection": {},
}


def deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    """Recursively merge override into base and return a new dictionary."""
    result = deepcopy(base)
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def _load_yaml_mapping(path: Path) -> dict[str, Any]:
    """Load a YAML file and require top-level mapping."""
    if not path.exists():
        return {}

    try:
        content = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise ValueError(f"Invalid YAML in {path}: {exc}") from exc
    except OSError as exc:
        raise ValueError(f"Failed to read config file {path}: {exc}") from exc

    if content is None:
        return {}
    if not isinstance(content, dict):
        raise ValueError(f"Config file {path} must contain a YAML mapping at top level")
    return content


def _parse_env_value(raw: str) -> Any:
    """Parse env value as YAML scalar/sequence/map when possible."""
    try:
        return yaml.safe_load(raw)
    except yaml.YAMLError:
        return raw


def _set_nested_value(target: dict[str, Any], path: list[str], value: Any) -> None:
    """Set nested value by path in a dictionary."""
    cursor = target
    for segment in path[:-1]:
        if segment not in cursor or not isinstance(cursor[segment], dict):
            cursor[segment] = {}
        cursor = cursor[segment]
    cursor[path[-1]] = value


def parse_env_overrides(env: Mapping[str, str] | None = None) -> dict[str, Any]:
    """Parse SPECIFY_CONFIG__* variables into nested config mapping.

    Example:
    - SPECIFY_CONFIG__SCOPE_DETECTION__WORK_ITEMS_MULTIPLIER=2
    """
    source = env or os.environ
    overrides: dict[str, Any] = {}

    for key, value in source.items():
        if not key.startswith(ENV_CONFIG_PREFIX):
            continue
        remainder = key[len(ENV_CONFIG_PREFIX):]
        if not remainder:
            continue
        segments = [segment.strip().lower() for segment in remainder.split("__") if segment.strip()]
        if not segments:
            continue
        _set_nested_value(overrides, segments, _parse_env_value(value))

    return overrides


def load_project_config(
    project_root: Path | None = None,
    *,
    env: Mapping[str, str] | None = None,
    defaults: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Load merged project configuration using deterministic precedence."""
    root = (project_root or Path.cwd()).resolve()
    merged = deepcopy(defaults if defaults is not None else DEFAULT_PROJECT_CONFIG)

    project_file = root / PROJECT_CONFIG_REL_PATH
    local_file = root / PROJECT_LOCAL_CONFIG_REL_PATH

    merged = deep_merge(merged, _load_yaml_mapping(project_file))
    merged = deep_merge(merged, _load_yaml_mapping(local_file))
    merged = deep_merge(merged, parse_env_overrides(env))

    return merged
