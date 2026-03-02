"""Schema and safety contract for native productivity cockpit configuration."""

from __future__ import annotations

from dataclasses import dataclass, field, fields
import json
from pathlib import Path, PurePosixPath
from typing import Any, Mapping

from .project_config import load_project_config


COCKPIT_CONFIG_FILE = ".cockpit.json"
COCKPIT_CONFIG_SCHEMA_VERSION = 1

DEFAULT_COCKPIT_NAME = "Spec Kit Productivity Cockpit"
DEFAULT_COCKPIT_VERSION = "1.0.0"
DEFAULT_COCKPIT_TASKS_PATH = "TASKS.md"
DEFAULT_COCKPIT_TASKS_FALLBACK_PATH = "TASKS.md"
DEFAULT_COCKPIT_MEMORY_PATH = "memory"
DEFAULT_COCKPIT_OUTPUT_PATH = "output"
DEFAULT_COCKPIT_ESSENTIAL_FILES = ["README.md"]

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8001

DEFAULT_FUZZY_TITLE_MATCH_THRESHOLD = 0.84
DEFAULT_STALE_AGE_DAYS = 30
DEFAULT_MAX_COMPREHENSIVE_SCAN_FILES = 80
DEFAULT_MAX_COMPREHENSIVE_SCAN_FILE_BYTES = 200_000
DEFAULT_COMMON_ENTITY_STOPWORDS = frozenset(
    {
        "The",
        "This",
        "That",
        "And",
        "For",
        "With",
        "Done",
        "TODO",
        "FIXME",
        "Action",
        "Review",
        "Update",
        "Task",
    }
)
DEFAULT_COMMON_ENTITY_VERBISH = frozenset(
    {
        "add",
        "check",
        "complete",
        "create",
        "draft",
        "existing",
        "finalize",
        "follow",
        "prepare",
        "review",
        "send",
        "share",
        "sync",
        "task",
        "update",
        "wait",
        "write",
    }
)


@dataclass(frozen=True)
class CockpitServiceConfig:
    host: str = DEFAULT_HOST
    port: int = DEFAULT_PORT


@dataclass(frozen=True)
class CockpitPathsConfig:
    tasks: str = DEFAULT_COCKPIT_TASKS_PATH
    tasks_fallback: str = DEFAULT_COCKPIT_TASKS_FALLBACK_PATH
    memory: str = DEFAULT_COCKPIT_MEMORY_PATH
    output: str = DEFAULT_COCKPIT_OUTPUT_PATH


@dataclass(frozen=True)
class CockpitPulseRulesConfig:
    essential_files: tuple[str, ...] = tuple(DEFAULT_COCKPIT_ESSENTIAL_FILES)
    min_folders: tuple[str, ...] = ()


@dataclass(frozen=True)
class CockpitAiConfig:
    mode: str = "cli"
    cli: str = ""
    args: tuple[str, ...] = ()
    provider: str = ""
    model: str = ""


@dataclass(frozen=True)
class ProductivityCockpitConfig:
    schema_version: int = COCKPIT_CONFIG_SCHEMA_VERSION
    name: str = DEFAULT_COCKPIT_NAME
    version: str = DEFAULT_COCKPIT_VERSION
    service: CockpitServiceConfig = field(default_factory=CockpitServiceConfig)
    paths: CockpitPathsConfig = field(default_factory=CockpitPathsConfig)
    pulse_rules: CockpitPulseRulesConfig = field(default_factory=CockpitPulseRulesConfig)
    ai: CockpitAiConfig = field(default_factory=CockpitAiConfig)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "name": self.name,
            "version": self.version,
            "service": {"host": self.service.host, "port": self.service.port},
            "paths": {
                "tasks": self.paths.tasks,
                "tasks_fallback": self.paths.tasks_fallback,
                "memory": self.paths.memory,
                "output": self.paths.output,
            },
            "pulse_rules": {
                "essential_files": list(self.pulse_rules.essential_files),
                "min_folders": list(self.pulse_rules.min_folders),
            },
            "ai": {
                "mode": self.ai.mode,
                "cli": self.ai.cli,
                "args": list(self.ai.args),
                "provider": self.ai.provider,
                "model": self.ai.model,
            },
        }


@dataclass(frozen=True)
class ProductivityUpdateConfig:
    fuzzy_title_match_threshold: float = DEFAULT_FUZZY_TITLE_MATCH_THRESHOLD
    default_stale_age_days: int = DEFAULT_STALE_AGE_DAYS
    max_comprehensive_scan_files: int = DEFAULT_MAX_COMPREHENSIVE_SCAN_FILES
    max_comprehensive_scan_file_bytes: int = DEFAULT_MAX_COMPREHENSIVE_SCAN_FILE_BYTES
    common_entity_stopwords: frozenset[str] = field(default_factory=lambda: DEFAULT_COMMON_ENTITY_STOPWORDS)
    common_entity_verbish: frozenset[str] = field(default_factory=lambda: DEFAULT_COMMON_ENTITY_VERBISH)

    def validate(self) -> None:
        if self.fuzzy_title_match_threshold <= 0 or self.fuzzy_title_match_threshold > 1:
            raise ValueError(
                "productivity_update.fuzzy_title_match_threshold must be > 0 and <= 1."
            )
        if self.default_stale_age_days < 1 or self.default_stale_age_days > 3650:
            raise ValueError("productivity_update.default_stale_age_days must be between 1 and 3650.")
        if self.max_comprehensive_scan_files < 1 or self.max_comprehensive_scan_files > 5000:
            raise ValueError("productivity_update.max_comprehensive_scan_files must be between 1 and 5000.")
        if (
            self.max_comprehensive_scan_file_bytes < 1024
            or self.max_comprehensive_scan_file_bytes > 20_000_000
        ):
            raise ValueError(
                "productivity_update.max_comprehensive_scan_file_bytes must be between 1024 and 20000000."
            )
        if not all(isinstance(item, str) and item.strip() for item in self.common_entity_stopwords):
            raise TypeError("productivity_update.common_entity_stopwords must contain non-empty strings.")
        if not all(isinstance(item, str) and item.strip() for item in self.common_entity_verbish):
            raise TypeError("productivity_update.common_entity_verbish must contain non-empty strings.")


def _coerce_mapping(value: Any, *, field_name: str) -> Mapping[str, Any]:
    if value is None:
        return {}
    if not isinstance(value, Mapping):
        raise TypeError(f"{field_name} must be a mapping.")
    return value


def _coerce_int(value: Any, *, field_name: str) -> int:
    if isinstance(value, bool):
        raise TypeError(f"{field_name} must be an integer.")
    if isinstance(value, int):
        return value
    if isinstance(value, str) and value.strip().isdigit():
        return int(value.strip())
    raise TypeError(f"{field_name} must be an integer.")


def _coerce_float(value: Any, *, field_name: str) -> float:
    if isinstance(value, bool):
        raise TypeError(f"{field_name} must be a number.")
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        normalized = value.strip()
        try:
            return float(normalized)
        except ValueError as exc:
            raise TypeError(f"{field_name} must be a number.") from exc
    raise TypeError(f"{field_name} must be a number.")


def _coerce_non_empty_string(value: Any, *, field_name: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a string.")
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{field_name} must not be empty.")
    return normalized


def _normalize_optional_string(value: Any, *, field_name: str) -> str:
    if value is None:
        return ""
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a string.")
    return value.strip()


def _validate_relative_path(raw: Any, *, field_name: str, default: str) -> str:
    if raw is None:
        normalized = default
    else:
        normalized = _coerce_non_empty_string(raw, field_name=field_name)

    normalized = normalized.replace("\\", "/")
    candidate = PurePosixPath(normalized)
    if candidate.is_absolute():
        raise ValueError(f"{field_name} must be a project-relative path, got absolute path '{normalized}'.")
    if ".." in candidate.parts:
        raise ValueError(f"{field_name} path traversal is not allowed: '{normalized}'.")
    if not candidate.parts:
        raise ValueError(f"{field_name} must not be empty.")
    return candidate.as_posix()


def _coerce_string_list(value: Any, *, field_name: str, default: tuple[str, ...]) -> tuple[str, ...]:
    if value is None:
        return default
    if not isinstance(value, (list, tuple)):
        raise TypeError(f"{field_name} must be a list of strings.")
    normalized: list[str] = []
    for item in value:
        if not isinstance(item, str):
            raise TypeError(f"{field_name} must contain only strings.")
        text = item.strip()
        if not text:
            continue
        normalized.append(text)
    return tuple(normalized)


def _assert_allowed_keys(raw: Mapping[str, Any], *, field_name: str, allowed: set[str]) -> None:
    unknown = sorted(set(raw.keys()) - allowed)
    if unknown:
        joined = ", ".join(unknown)
        raise ValueError(f"Unknown {field_name} keys: {joined}")


def cockpit_config_from_mapping(
    raw_config: Mapping[str, Any] | None,
    *,
    default_tasks_path: str = DEFAULT_COCKPIT_TASKS_PATH,
    default_host: str = DEFAULT_HOST,
    default_port: int = DEFAULT_PORT,
) -> ProductivityCockpitConfig:
    """Normalize and validate `.cockpit.json` payload."""
    raw = _coerce_mapping(raw_config, field_name="cockpit config")
    _assert_allowed_keys(
        raw,
        field_name="cockpit config",
        allowed={"schema_version", "name", "version", "service", "paths", "pulse_rules", "ai"},
    )

    schema_version = _coerce_int(raw.get("schema_version", COCKPIT_CONFIG_SCHEMA_VERSION), field_name="schema_version")
    if schema_version != COCKPIT_CONFIG_SCHEMA_VERSION:
        raise ValueError(
            f"Unsupported cockpit schema_version '{schema_version}'. "
            f"Expected {COCKPIT_CONFIG_SCHEMA_VERSION}."
        )

    name = _normalize_optional_string(raw.get("name", DEFAULT_COCKPIT_NAME), field_name="name") or DEFAULT_COCKPIT_NAME
    version = _normalize_optional_string(raw.get("version", DEFAULT_COCKPIT_VERSION), field_name="version") or DEFAULT_COCKPIT_VERSION

    service_raw = _coerce_mapping(raw.get("service"), field_name="service")
    _assert_allowed_keys(service_raw, field_name="service", allowed={"host", "port"})
    host = _normalize_optional_string(service_raw.get("host", default_host), field_name="service.host") or default_host
    port = _coerce_int(service_raw.get("port", default_port), field_name="service.port")
    if port < 1 or port > 65535:
        raise ValueError("service.port must be between 1 and 65535.")
    service = CockpitServiceConfig(host=host, port=port)

    paths_raw = _coerce_mapping(raw.get("paths"), field_name="paths")
    _assert_allowed_keys(paths_raw, field_name="paths", allowed={"tasks", "tasks_fallback", "memory", "output"})
    paths = CockpitPathsConfig(
        tasks=_validate_relative_path(
            paths_raw.get("tasks"),
            field_name="paths.tasks",
            default=default_tasks_path,
        ),
        tasks_fallback=_validate_relative_path(
            paths_raw.get("tasks_fallback"),
            field_name="paths.tasks_fallback",
            default=DEFAULT_COCKPIT_TASKS_FALLBACK_PATH,
        ),
        memory=_validate_relative_path(
            paths_raw.get("memory"),
            field_name="paths.memory",
            default=DEFAULT_COCKPIT_MEMORY_PATH,
        ),
        output=_validate_relative_path(
            paths_raw.get("output"),
            field_name="paths.output",
            default=DEFAULT_COCKPIT_OUTPUT_PATH,
        ),
    )

    pulse_raw = _coerce_mapping(raw.get("pulse_rules"), field_name="pulse_rules")
    _assert_allowed_keys(pulse_raw, field_name="pulse_rules", allowed={"essential_files", "min_folders"})
    essential_files = _coerce_string_list(
        pulse_raw.get("essential_files"),
        field_name="pulse_rules.essential_files",
        default=tuple(DEFAULT_COCKPIT_ESSENTIAL_FILES),
    )
    min_folders = _coerce_string_list(
        pulse_raw.get("min_folders"),
        field_name="pulse_rules.min_folders",
        default=(),
    )
    pulse_rules = CockpitPulseRulesConfig(essential_files=essential_files, min_folders=min_folders)

    ai_raw = _coerce_mapping(raw.get("ai"), field_name="ai")
    _assert_allowed_keys(ai_raw, field_name="ai", allowed={"mode", "cli", "args", "provider", "model"})
    mode = _normalize_optional_string(ai_raw.get("mode", "cli"), field_name="ai.mode").lower() or "cli"
    if mode not in {"cli", "api"}:
        raise ValueError("ai.mode must be either 'cli' or 'api'.")
    cli = _normalize_optional_string(ai_raw.get("cli", ""), field_name="ai.cli")
    args = _coerce_string_list(ai_raw.get("args"), field_name="ai.args", default=())
    provider = _normalize_optional_string(ai_raw.get("provider", ""), field_name="ai.provider")
    model = _normalize_optional_string(ai_raw.get("model", ""), field_name="ai.model")
    ai = CockpitAiConfig(mode=mode, cli=cli, args=args, provider=provider, model=model)

    return ProductivityCockpitConfig(
        schema_version=schema_version,
        name=name,
        version=version,
        service=service,
        paths=paths,
        pulse_rules=pulse_rules,
        ai=ai,
    )


def default_cockpit_config_payload(*, tasks_path: str, host: str, port: int) -> dict[str, Any]:
    """Build default cockpit payload validated against the A4 schema."""
    normalized = cockpit_config_from_mapping(
        {
            "name": DEFAULT_COCKPIT_NAME,
            "version": DEFAULT_COCKPIT_VERSION,
            "service": {"host": host, "port": port},
            "paths": {
                "tasks": tasks_path,
                "tasks_fallback": DEFAULT_COCKPIT_TASKS_FALLBACK_PATH,
                "memory": DEFAULT_COCKPIT_MEMORY_PATH,
                "output": DEFAULT_COCKPIT_OUTPUT_PATH,
            },
            "pulse_rules": {"essential_files": DEFAULT_COCKPIT_ESSENTIAL_FILES, "min_folders": []},
            "ai": {"mode": "cli", "cli": "", "args": []},
        },
        default_tasks_path=tasks_path,
        default_host=host,
        default_port=port,
    )
    return normalized.to_dict()


def ensure_path_within_project_root(project_root: Path, path: Path, *, field_name: str) -> Path:
    """Resolve a path and enforce project-root sandboxing."""
    root = project_root.resolve()
    candidate = path.resolve()
    try:
        candidate.relative_to(root)
    except ValueError as exc:
        raise ValueError(f"{field_name} points outside project root: {path}") from exc
    return candidate


def resolve_project_relative_path(project_root: Path, raw: str, *, field_name: str) -> Path:
    """Resolve a required project-relative path with traversal protection."""
    root = project_root.resolve()
    normalized = _validate_relative_path(raw, field_name=field_name, default="")
    candidate = (root / normalized).resolve()
    return ensure_path_within_project_root(root, candidate, field_name=field_name)


def resolve_optional_project_relative_path(
    project_root: Path, raw: str | None, *, field_name: str
) -> Path | None:
    """Resolve optional project-relative path with traversal protection."""
    if raw is None:
        return None
    text = str(raw).strip()
    if not text:
        return None
    return resolve_project_relative_path(project_root, text, field_name=field_name)


def load_cockpit_config(
    project_root: Path,
    *,
    file_name: str = COCKPIT_CONFIG_FILE,
) -> ProductivityCockpitConfig | None:
    """Load and validate `.cockpit.json` from project root."""
    root = project_root.resolve()
    cockpit_path = root / file_name
    if not cockpit_path.exists():
        return None
    ensure_path_within_project_root(root, cockpit_path, field_name=file_name)
    if cockpit_path.is_symlink():
        ensure_path_within_project_root(root, cockpit_path.resolve(), field_name=file_name)

    try:
        payload = json.loads(cockpit_path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise ValueError(f"Could not read .cockpit.json: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"Could not parse .cockpit.json: {exc.msg}") from exc

    return cockpit_config_from_mapping(raw_config=payload)


def productivity_update_config_from_mapping(raw_config: Mapping[str, Any] | None) -> ProductivityUpdateConfig:
    """Build productivity update runtime config from project mapping."""
    if raw_config is None:
        config = ProductivityUpdateConfig()
        config.validate()
        return config
    if not isinstance(raw_config, Mapping):
        raise ValueError("productivity_update config must be a mapping.")

    allowed_fields = {field_info.name for field_info in fields(ProductivityUpdateConfig)}
    unknown = sorted(set(raw_config.keys()) - allowed_fields)
    if unknown:
        joined = ", ".join(unknown)
        raise ValueError(f"Unknown productivity_update config keys: {joined}")

    data = dict(raw_config)
    if "fuzzy_title_match_threshold" in data:
        data["fuzzy_title_match_threshold"] = _coerce_float(
            data["fuzzy_title_match_threshold"],
            field_name="productivity_update.fuzzy_title_match_threshold",
        )
    if "default_stale_age_days" in data:
        data["default_stale_age_days"] = _coerce_int(
            data["default_stale_age_days"],
            field_name="productivity_update.default_stale_age_days",
        )
    if "max_comprehensive_scan_files" in data:
        data["max_comprehensive_scan_files"] = _coerce_int(
            data["max_comprehensive_scan_files"],
            field_name="productivity_update.max_comprehensive_scan_files",
        )
    if "max_comprehensive_scan_file_bytes" in data:
        data["max_comprehensive_scan_file_bytes"] = _coerce_int(
            data["max_comprehensive_scan_file_bytes"],
            field_name="productivity_update.max_comprehensive_scan_file_bytes",
        )
    if "common_entity_stopwords" in data:
        data["common_entity_stopwords"] = frozenset(
            _coerce_string_list(
                data["common_entity_stopwords"],
                field_name="productivity_update.common_entity_stopwords",
                default=tuple(DEFAULT_COMMON_ENTITY_STOPWORDS),
            )
        )
    if "common_entity_verbish" in data:
        data["common_entity_verbish"] = frozenset(
            _coerce_string_list(
                data["common_entity_verbish"],
                field_name="productivity_update.common_entity_verbish",
                default=tuple(DEFAULT_COMMON_ENTITY_VERBISH),
            )
        )

    config = ProductivityUpdateConfig(**data)
    config.validate()
    return config


def load_productivity_update_config(
    project_root: Path | None = None,
    *,
    env: Mapping[str, str] | None = None,
) -> ProductivityUpdateConfig:
    """Load productivity update runtime config from merged project config."""
    project_config = load_project_config(project_root=project_root, env=env)
    raw = project_config.get("productivity_update", {})
    return productivity_update_config_from_mapping(raw)
