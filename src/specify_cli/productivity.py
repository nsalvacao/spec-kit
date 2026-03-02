"""Native productivity flows (A1 start + A2 update scopes)."""

from __future__ import annotations

from datetime import date
from difflib import SequenceMatcher
from dataclasses import dataclass, field
import json
import os
from pathlib import Path
import re
import socket
import subprocess
import sys
import time
from typing import Any, Callable, Iterable, TextIO
from urllib.error import URLError
from urllib.request import Request, urlopen
import webbrowser

from .productivity_config import (
    DEFAULT_HOST as PRODUCTIVITY_CONFIG_DEFAULT_HOST,
    DEFAULT_PORT as PRODUCTIVITY_CONFIG_DEFAULT_PORT,
    ProductivityUpdateConfig,
    default_cockpit_config_payload,
    ensure_path_within_project_root,
    load_cockpit_config,
    load_productivity_update_config,
    resolve_optional_project_relative_path,
    resolve_project_relative_path,
)


CANONICAL_FEATURE_BRANCH_RE = re.compile(r"^(?P<prefix>\d{3})-(?P<slug>[a-z0-9]+(?:-[a-z0-9]+)*)$")
PRODUCTIVITY_SERVICE_NAME = "specify-productivity-cockpit"
DEFAULT_HOST = PRODUCTIVITY_CONFIG_DEFAULT_HOST
DEFAULT_PORT = PRODUCTIVITY_CONFIG_DEFAULT_PORT
PORT_SCAN_LIMIT = 25
BRIDGE_START_TIMEOUT_SECONDS = 10.0

DEFAULT_TASKS_TEMPLATE = """# Tasks

## Active

## Waiting On

## Someday

## Done
"""

DEFAULT_CLAUDE_TEMPLATE = """# Memory

## Me
- Name:
- Role:
- Team:

## People
| Who | Role |
|-----|------|

## Terms
| Term | Meaning |
|------|---------|

## Projects
| Name | What |
|------|------|

## Preferences
- Communication:
- Meeting constraints:
- Other:
"""

DEFAULT_BOOTSTRAP_TEMPLATE = """# Memory Bootstrap (First Run)

Use this file to seed your memory baseline quickly.

## 1) People (nicknames -> full names)
- Example: Todd -> Todd Martinez (Finance)

## 2) Terms (acronyms / internal language)
- Example: PSR -> Pipeline Status Report

## 3) Projects (codename -> meaning)
- Example: Phoenix -> DB migration workstream

## 4) Current priorities
- What are your top 3 active outcomes this week?

After filling this file, move confirmed items into:
- `CLAUDE.md` (hot memory)
- `memory/glossary.md`
- `memory/people/`
- `memory/projects/`
"""

DEFAULT_MEMORY_FILES: dict[str, str] = {
    "memory/glossary.md": "# Glossary\n\n## Acronyms\n\n## Internal Terms\n\n## Project Codenames\n",
    "memory/people/README.md": "# People\n\nOne file per person.\n",
    "memory/projects/README.md": "# Projects\n\nOne file per project.\n",
    "memory/context/company.md": "# Company Context\n\n## Teams\n\n## Tools\n\n## Processes\n",
}


@dataclass
class ScaffoldResult:
    project_root: Path
    created: list[str] = field(default_factory=list)
    existing: list[str] = field(default_factory=list)
    bootstrap_required: bool = False
    tasks_path_for_cockpit: str = "TASKS.md"
    config_path: Path | None = None


@dataclass
class StartOutcome:
    ok: bool
    project_root: Path
    url: str
    host: str
    port: int
    server_reused: bool
    server_started: bool
    browser_opened: bool
    browser_method: str | None
    scaffold: ScaffoldResult
    notes: list[str] = field(default_factory=list)
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "project_root": str(self.project_root),
            "url": self.url,
            "host": self.host,
            "port": self.port,
            "server_reused": self.server_reused,
            "server_started": self.server_started,
            "browser_opened": self.browser_opened,
            "browser_method": self.browser_method,
            "scaffold": {
                "created": self.scaffold.created,
                "existing": self.scaffold.existing,
                "bootstrap_required": self.scaffold.bootstrap_required,
                "tasks_path_for_cockpit": self.scaffold.tasks_path_for_cockpit,
                "config_path": str(self.scaffold.config_path) if self.scaffold.config_path else None,
            },
            "notes": self.notes,
            "error": self.error,
        }


def _safe_write_if_missing(path: Path, content: str) -> bool:
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with path.open("x", encoding="utf-8") as handle:
            handle.write(content)
    except FileExistsError:
        return False
    except OSError as exc:
        raise RuntimeError(f"Could not write '{path}': {exc}") from exc
    return True


def _current_branch(project_root: Path) -> str | None:
    env_override = os.getenv("SPECIFY_FEATURE", "").strip()
    if env_override:
        return env_override
    try:
        result = subprocess.run(
            ["git", "-C", str(project_root), "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError:
        return None

    if result.returncode != 0:
        return None
    branch = (result.stdout or "").strip()
    return branch or None


def _resolve_feature_tasks_path(project_root: Path) -> str | None:
    branch = _current_branch(project_root)
    if not branch:
        return None
    if not CANONICAL_FEATURE_BRANCH_RE.fullmatch(branch):
        return None
    feature_tasks = project_root / "specs" / branch / "tasks.md"
    if not feature_tasks.exists():
        return None
    return str(feature_tasks.relative_to(project_root))


def _default_cockpit_config(*, tasks_path: str, host: str, port: int) -> dict[str, Any]:
    # A4 (#203) contract keeps ai.cli neutral by default until a CLI is explicitly chosen.
    return default_cockpit_config_payload(tasks_path=tasks_path, host=host, port=port)


def prepare_productivity_scaffold(project_root: Path, *, host: str, port: int) -> ScaffoldResult:
    root = project_root.resolve()
    if not root.exists() or not root.is_dir():
        raise ValueError(f"Project root does not exist: {root}")

    result = ScaffoldResult(project_root=root)

    tasks_file = root / "TASKS.md"
    claude_file = root / "CLAUDE.md"
    memory_dir = root / "memory"
    cockpit_config = root / ".cockpit.json"

    had_claude = claude_file.exists()
    had_memory = memory_dir.exists()
    result.bootstrap_required = not had_claude and not had_memory

    if _safe_write_if_missing(tasks_file, DEFAULT_TASKS_TEMPLATE):
        result.created.append("TASKS.md")
    else:
        result.existing.append("TASKS.md")

    if _safe_write_if_missing(claude_file, DEFAULT_CLAUDE_TEMPLATE):
        result.created.append("CLAUDE.md")
    else:
        result.existing.append("CLAUDE.md")

    if not memory_dir.exists():
        memory_dir.mkdir(parents=True, exist_ok=True)
        result.created.append("memory/")
    else:
        result.existing.append("memory/")

    for rel_path, content in DEFAULT_MEMORY_FILES.items():
        target = root / rel_path
        if _safe_write_if_missing(target, content):
            result.created.append(rel_path)
        else:
            result.existing.append(rel_path)

    if result.bootstrap_required:
        bootstrap_file = root / "memory" / "bootstrap.md"
        if _safe_write_if_missing(bootstrap_file, DEFAULT_BOOTSTRAP_TEMPLATE):
            result.created.append("memory/bootstrap.md")
        else:
            result.existing.append("memory/bootstrap.md")

    feature_tasks_path = _resolve_feature_tasks_path(root)
    tasks_path = feature_tasks_path or "TASKS.md"
    result.tasks_path_for_cockpit = tasks_path

    if not cockpit_config.exists():
        payload = _default_cockpit_config(tasks_path=tasks_path, host=host, port=port)
        cockpit_config_payload = json.dumps(payload, indent=2) + "\n"
        if _safe_write_if_missing(cockpit_config, cockpit_config_payload):
            result.created.append(".cockpit.json")
        else:
            result.existing.append(".cockpit.json")
    else:
        result.existing.append(".cockpit.json")
    result.config_path = cockpit_config

    return result


def _probe_running_bridge(host: str, port: int, timeout_seconds: float = 0.35) -> bool:
    url = f"http://{host}:{port}/api/status"
    request = Request(url, headers={"Accept": "application/json"})
    try:
        with urlopen(request, timeout=timeout_seconds) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (URLError, OSError, TimeoutError, json.JSONDecodeError, ValueError):
        return False
    return payload.get("service") == PRODUCTIVITY_SERVICE_NAME


def _port_is_free(host: str, port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.35)
        return sock.connect_ex((host, port)) != 0


def resolve_runtime_port(host: str, preferred_port: int) -> tuple[int, bool]:
    for port in range(preferred_port, preferred_port + PORT_SCAN_LIMIT):
        if _probe_running_bridge(host, port):
            return port, True
        if _port_is_free(host, port):
            return port, False
    raise RuntimeError(
        f"Could not find an available cockpit port in range {preferred_port}-{preferred_port + PORT_SCAN_LIMIT - 1}."
    )


def _is_wsl() -> bool:
    if os.getenv("WSL_DISTRO_NAME"):
        return True
    try:
        return "microsoft" in Path("/proc/version").read_text(encoding="utf-8").lower()
    except OSError:
        return False


def open_dashboard_url(url: str) -> tuple[bool, str | None]:
    try:
        if webbrowser.open(url, new=2):
            return True, "webbrowser"
    except Exception:
        pass

    candidates: list[tuple[str, list[str]]] = []
    if sys.platform.startswith("darwin"):
        candidates.append(("open", ["open", url]))
    elif sys.platform.startswith("win"):
        startfile = getattr(os, "startfile", None)
        if callable(startfile):
            try:
                startfile(url)
                return True, "os.startfile"
            except OSError:
                pass
        candidates.append(("explorer", ["explorer.exe", url]))
    else:
        if _is_wsl():
            candidates.append(("wslview", ["wslview", url]))
            candidates.append(("explorer", ["explorer.exe", url]))
        candidates.append(("xdg-open", ["xdg-open", url]))

    for method, command in candidates:
        try:
            subprocess.Popen(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return True, method
        except OSError:
            continue
    return False, None


def _launch_bridge_process(project_root: Path, host: str, port: int) -> tuple[subprocess.Popen[str], TextIO]:
    log_dir = project_root / ".spec-kit" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "productivity-cockpit.log"
    log_stream = open(log_file, "a", encoding="utf-8")

    command = [
        sys.executable,
        "-m",
        "specify_cli.productivity_bridge",
        "--project-root",
        str(project_root),
        "--host",
        host,
        "--port",
        str(port),
    ]

    popen_kwargs: dict[str, Any] = {
        "stdout": log_stream,
        "stderr": log_stream,
        "text": True,
        "cwd": str(project_root),
    }

    if os.name == "nt":
        popen_kwargs["creationflags"] = subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP
    else:
        popen_kwargs["start_new_session"] = True

    process = subprocess.Popen(command, **popen_kwargs)
    return process, log_stream


def ensure_bridge_running(project_root: Path, host: str, port: int) -> tuple[bool, bool]:
    if _probe_running_bridge(host, port):
        return True, True

    process, log_stream = _launch_bridge_process(project_root, host, port)
    try:
        start = time.monotonic()
        while time.monotonic() - start < BRIDGE_START_TIMEOUT_SECONDS:
            if _probe_running_bridge(host, port):
                return True, False
            if process.poll() is not None:
                break
            time.sleep(0.2)
        return False, False
    finally:
        log_stream.close()


def run_productivity_start(
    *,
    project_root: Path,
    host: str = DEFAULT_HOST,
    preferred_port: int = DEFAULT_PORT,
    start_server: bool = True,
    open_browser: bool = True,
) -> StartOutcome:
    root = project_root.resolve()
    scaffold = prepare_productivity_scaffold(root, host=host, port=preferred_port)
    reused = False
    if start_server:
        port, reused = resolve_runtime_port(host, preferred_port)
    else:
        port = preferred_port
    url = f"http://{host}:{port}"
    notes: list[str] = []

    server_started = False
    server_reused = reused
    if start_server:
        ok, reused_after_start = ensure_bridge_running(root, host, port)
        if not ok:
            return StartOutcome(
                ok=False,
                project_root=root,
                url=url,
                host=host,
                port=port,
                server_reused=server_reused,
                server_started=False,
                browser_opened=False,
                browser_method=None,
                scaffold=scaffold,
                notes=notes,
                error=(
                    "Cockpit bridge did not become ready in time. "
                    "Check .spec-kit/logs/productivity-cockpit.log and retry."
                ),
            )
        server_reused = reused_after_start
        server_started = not reused_after_start
    else:
        notes.append("Server launch skipped by option.")

    browser_opened = False
    browser_method: str | None = None
    if open_browser and start_server:
        browser_opened, browser_method = open_dashboard_url(url)
        if not browser_opened:
            notes.append(f"Could not open browser automatically. Open {url} manually.")
    elif not open_browser:
        notes.append(f"Browser opening skipped by option. Cockpit URL: {url}")

    if scaffold.bootstrap_required:
        notes.append("First-run memory bootstrap is pending: review memory/bootstrap.md.")

    return StartOutcome(
        ok=True,
        project_root=root,
        url=url,
        host=host,
        port=port,
        server_reused=server_reused,
        server_started=server_started,
        browser_opened=browser_opened,
        browser_method=browser_method,
        scaffold=scaffold,
        notes=notes,
    )


TASK_SECTION_ORDER = ("Active", "Waiting On", "Someday", "Done")
TASK_LINE_RE = re.compile(r"^\s*-\s*\[(?P<checked>[ xX])\]\s*(?P<body>.+?)\s*$")
DUE_DATE_RE = re.compile(r"(?i)\bdue[:\s]+(?P<date>\d{4}-\d{2}-\d{2})\b")
SINCE_DATE_RE = re.compile(r"(?i)\bsince[:\s]+(?P<date>\d{4}-\d{2}-\d{2})\b")
URL_RE = re.compile(r"https?://[^\s)>\]]+")
ACRONYM_RE = re.compile(r"\b[A-Z][A-Z0-9]{1,}\b")
NAME_RE = re.compile(r"\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2}\b")
TODO_HINT_RE = re.compile(r"(?i)\b(todo|fixme|action item|action:|follow[- ]up)\b")
MAX_EXTERNAL_TASK_TITLE_CHARS = 240
COMPREHENSIVE_SKIP_DIRS = {
    ".git",
    ".venv",
    "venv",
    "node_modules",
    ".mypy_cache",
    ".ruff_cache",
    ".pytest_cache",
    ".spec-kit",
}


@dataclass
class TaskRecord:
    section: str
    title: str
    body: str
    line_number: int
    checked: bool
    due_date: date | None = None
    since_date: date | None = None


@dataclass
class ExternalTaskRecord:
    title: str
    source: str
    state: str = "open"


@dataclass
class UpdateOutcome:
    ok: bool
    mode: str
    project_root: Path
    tasks_path: Path | None
    memory_dir: Path | None
    task_sync: dict[str, Any] = field(default_factory=dict)
    stale_findings: list[dict[str, Any]] = field(default_factory=list)
    memory_gaps: list[dict[str, Any]] = field(default_factory=list)
    memory_enrichment: list[dict[str, Any]] = field(default_factory=list)
    comprehensive: dict[str, Any] | None = None
    applied: dict[str, list[str]] = field(default_factory=lambda: {"tasks": [], "memory": []})
    notes: list[str] = field(default_factory=list)
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "mode": self.mode,
            "project_root": str(self.project_root),
            "tasks_path": str(self.tasks_path) if self.tasks_path else None,
            "memory_dir": str(self.memory_dir) if self.memory_dir else None,
            "task_sync": self.task_sync,
            "stale_findings": self.stale_findings,
            "memory_gaps": self.memory_gaps,
            "memory_enrichment": self.memory_enrichment,
            "comprehensive": self.comprehensive,
            "applied": self.applied,
            "notes": self.notes,
            "error": self.error,
        }


def _normalize_title(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()


def _title_similarity(a: str, b: str) -> float:
    if not a or not b:
        return 0.0
    return SequenceMatcher(a=a, b=b).ratio()


def _parse_iso_date(match: re.Match[str] | None) -> date | None:
    if not match:
        return None
    raw = match.group("date")
    try:
        return date.fromisoformat(raw)
    except ValueError:
        return None


def _strip_task_markup(body: str) -> str:
    stripped = re.sub(r"\*\*(.*?)\*\*", r"\1", body)
    stripped = re.sub(r"~~(.*?)~~", r"\1", stripped)
    stripped = re.sub(r"`([^`]*)`", r"\1", stripped)
    return stripped.strip()


def _task_title_from_body(body: str) -> str:
    plain = _strip_task_markup(body)
    for separator in (" - ", " — ", " – "):
        if separator in plain:
            title = plain.split(separator, 1)[0].strip()
            if title:
                return title
    return plain


def _resolve_update_paths(project_root: Path, notes: list[str]) -> tuple[Path, Path]:
    cockpit_config = load_cockpit_config(project_root)
    tasks_raw = cockpit_config.paths.tasks if cockpit_config else None
    tasks_fallback_raw = cockpit_config.paths.tasks_fallback if cockpit_config else None
    memory_raw = cockpit_config.paths.memory if cockpit_config else None

    try:
        tasks_candidate = resolve_optional_project_relative_path(
            project_root,
            tasks_raw,
            field_name="paths.tasks",
        )
    except ValueError as exc:
        raise ValueError(f"Invalid cockpit config path for tasks: {exc}") from exc

    if tasks_candidate and tasks_candidate.exists():
        tasks_path = tasks_candidate
    else:
        if tasks_candidate and not tasks_candidate.exists():
            notes.append(f"Configured tasks path not found: {tasks_candidate}. Falling back.")

        tasks_fallback_candidate = None
        if tasks_fallback_raw:
            try:
                tasks_fallback_candidate = resolve_optional_project_relative_path(
                    project_root,
                    tasks_fallback_raw,
                    field_name="paths.tasks_fallback",
                )
            except ValueError as exc:
                raise ValueError(f"Invalid cockpit config path for tasks_fallback: {exc}") from exc

        if tasks_fallback_candidate and tasks_fallback_candidate.exists():
            tasks_path = tasks_fallback_candidate
        else:
            if tasks_fallback_candidate and not tasks_fallback_candidate.exists():
                notes.append(f"Configured tasks fallback path not found: {tasks_fallback_candidate}.")
            feature_relative = _resolve_feature_tasks_path(project_root)
            if feature_relative:
                tasks_path = resolve_project_relative_path(
                    project_root,
                    feature_relative,
                    field_name="feature tasks path",
                )
            else:
                tasks_path = resolve_project_relative_path(
                    project_root,
                    "TASKS.md",
                    field_name="default tasks path",
                )

    try:
        memory_candidate = resolve_optional_project_relative_path(
            project_root,
            memory_raw,
            field_name="paths.memory",
        )
    except ValueError as exc:
        raise ValueError(f"Invalid cockpit config path for memory: {exc}") from exc

    if memory_candidate:
        memory_dir = memory_candidate
    else:
        memory_dir = resolve_project_relative_path(
            project_root,
            "memory",
            field_name="default memory path",
        )

    tasks_path = ensure_path_within_project_root(project_root, tasks_path, field_name="tasks path")
    memory_dir = ensure_path_within_project_root(project_root, memory_dir, field_name="memory path")
    return tasks_path, memory_dir


def _parse_tasks(tasks_path: Path) -> list[TaskRecord]:
    lines = tasks_path.read_text(encoding="utf-8").splitlines()
    records: list[TaskRecord] = []
    section: str | None = None

    for line_number, line in enumerate(lines, start=1):
        heading = re.match(r"^\s*##\s+(?P<label>.+?)\s*$", line)
        if heading:
            label = heading.group("label").strip()
            section = label if label in TASK_SECTION_ORDER else None
            continue
        if not section:
            continue
        match = TASK_LINE_RE.match(line)
        if not match:
            continue
        body = match.group("body").strip()
        checked = match.group("checked").lower() == "x"
        due_date = _parse_iso_date(DUE_DATE_RE.search(body))
        since_date = _parse_iso_date(SINCE_DATE_RE.search(body))
        title = _task_title_from_body(body)
        records.append(
            TaskRecord(
                section=section,
                title=title,
                body=body,
                line_number=line_number,
                checked=checked,
                due_date=due_date,
                since_date=since_date,
            )
        )
    return records


def _coerce_external_task(item: Any, source_hint: str) -> ExternalTaskRecord | None:
    if isinstance(item, str) and item.strip():
        normalized_title = _normalize_external_title(item)
        if not normalized_title:
            return None
        return ExternalTaskRecord(title=normalized_title, source=source_hint, state="open")
    if not isinstance(item, dict):
        return None

    title = _normalize_external_title(item.get("title", ""))
    if not title:
        return None
    raw_state = str(item.get("state", "open")).strip().lower()
    state = "closed" if raw_state in {"closed", "done", "completed"} else "open"
    source = " ".join(str(item.get("source", source_hint)).split()).strip() or source_hint
    return ExternalTaskRecord(title=title, source=source, state=state)


def _normalize_external_title(value: Any) -> str:
    title = " ".join(str(value).split()).strip()
    if not title:
        return ""
    if len(title) > MAX_EXTERNAL_TASK_TITLE_CHARS:
        title = title[: MAX_EXTERNAL_TASK_TITLE_CHARS - 3].rstrip() + "..."
    return title


def _load_external_tasks_from_file(external_tasks_file: Path, notes: list[str]) -> list[ExternalTaskRecord]:
    try:
        payload = json.loads(external_tasks_file.read_text(encoding="utf-8"))
    except OSError as exc:
        raise ValueError(f"Could not read external tasks file: {external_tasks_file} ({exc})") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"Could not parse external tasks file: {external_tasks_file} ({exc.msg})") from exc

    if not isinstance(payload, list):
        raise ValueError(f"External tasks file must contain a JSON list: {external_tasks_file}")

    records: list[ExternalTaskRecord] = []
    for item in payload:
        record = _coerce_external_task(item, f"file:{external_tasks_file.name}")
        if record:
            records.append(record)
    if len(records) < len(payload):
        notes.append(
            f"Ignored {len(payload) - len(records)} invalid external task entries in {external_tasks_file.name}."
        )
    return records


def _load_external_tasks_from_github(project_root: Path, notes: list[str]) -> list[ExternalTaskRecord]:
    if not (project_root / ".git").exists():
        return []

    try:
        result = subprocess.run(
            [
                "gh",
                "issue",
                "list",
                "--assignee",
                "@me",
                "--state",
                "all",
                "--limit",
                "100",
                "--json",
                "title,url,state",
            ],
            capture_output=True,
            text=True,
            check=False,
            cwd=str(project_root),
            timeout=8.0,
        )
    except FileNotFoundError:
        notes.append("GitHub sync skipped: gh CLI is not available.")
        return []
    except subprocess.TimeoutExpired:
        notes.append("GitHub sync timed out and was skipped.")
        return []

    if result.returncode != 0:
        stderr = (result.stderr or "").strip()
        detail = stderr.splitlines()[0] if stderr else "unknown gh issue list error"
        notes.append(f"GitHub sync skipped: {detail}")
        return []

    try:
        payload = json.loads(result.stdout or "[]")
    except json.JSONDecodeError:
        notes.append("GitHub sync skipped: invalid JSON returned by gh CLI.")
        return []

    if not isinstance(payload, list):
        return []

    records: list[ExternalTaskRecord] = []
    for item in payload:
        record = _coerce_external_task(item, "github")
        if record:
            records.append(record)
    return records


def _best_local_match(external_title: str, local_tasks: list[TaskRecord]) -> tuple[TaskRecord | None, float]:
    target = _normalize_title(external_title)
    if not target:
        return None, 0.0

    best_task: TaskRecord | None = None
    best_score = 0.0
    for local in local_tasks:
        candidate = _normalize_title(local.title)
        if not candidate:
            continue
        score = 1.0 if candidate == target else _title_similarity(candidate, target)
        if target in candidate or candidate in target:
            score = max(score, 0.92)
        if score > best_score:
            best_score = score
            best_task = local
    return best_task, best_score


def _analyze_task_sync(
    *,
    local_tasks: list[TaskRecord],
    external_tasks: list[ExternalTaskRecord],
    fuzzy_match_threshold: float,
) -> dict[str, Any]:
    active_local = [task for task in local_tasks if not task.checked and task.section in {"Active", "Waiting On", "Someday"}]
    additions: list[dict[str, Any]] = []
    duplicates: list[dict[str, Any]] = []
    completion_candidates: list[dict[str, Any]] = []

    seen_addition_norms: set[str] = set()
    for external in external_tasks:
        matched, score = _best_local_match(external.title, active_local)
        normalized = _normalize_title(external.title)

        if matched and score >= fuzzy_match_threshold:
            duplicates.append(
                {
                    "external_title": external.title,
                    "local_title": matched.title,
                    "local_section": matched.section,
                    "match_score": round(score, 3),
                    "source": external.source,
                }
            )
            if external.state == "closed" and matched.section == "Active":
                completion_candidates.append(
                    {
                        "title": matched.title,
                        "line_number": matched.line_number,
                        "source": external.source,
                        "reason": "matched_closed_external_task",
                    }
                )
            continue

        if external.state == "closed":
            continue

        if normalized in seen_addition_norms:
            continue
        seen_addition_norms.add(normalized)
        additions.append(
            {
                "title": external.title,
                "source": external.source,
                "state": external.state,
            }
        )

    return {
        "external_total": len(external_tasks),
        "additions": additions,
        "duplicates": duplicates,
        "completion_candidates": completion_candidates,
    }


def _task_has_context(task: TaskRecord) -> bool:
    lower = f" {task.body.lower()} "
    has_person_hint = " for " in lower or "@" in task.body
    has_project_hint = "#" in task.body or "project:" in lower or "specs/" in lower
    return has_person_hint or has_project_hint


def _analyze_stale_tasks(local_tasks: list[TaskRecord], *, stale_days: int) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    today = date.today()

    for task in local_tasks:
        if task.checked or task.section != "Active":
            continue

        reasons: list[str] = []
        payload: dict[str, Any] = {
            "title": task.title,
            "line_number": task.line_number,
            "section": task.section,
            "reasons": reasons,
        }

        if task.due_date and task.due_date < today:
            reasons.append("due_date_past")
            payload["due_date"] = task.due_date.isoformat()

        if task.since_date:
            age_days = (today - task.since_date).days
            payload["since_date"] = task.since_date.isoformat()
            payload["age_days"] = age_days
            if age_days >= stale_days:
                reasons.append("active_too_long")

        if not _task_has_context(task):
            reasons.append("missing_context")

        if reasons:
            findings.append(payload)

    return findings


def _iter_memory_markdown_files(project_root: Path, memory_dir: Path) -> Iterable[Path]:
    claude_file = project_root / "CLAUDE.md"
    if claude_file.exists():
        yield claude_file
    if memory_dir.exists():
        for candidate in sorted(memory_dir.rglob("*.md")):
            if candidate.is_file():
                yield candidate


def _build_memory_corpus(project_root: Path, memory_dir: Path) -> str:
    chunks: list[str] = []
    for file_path in _iter_memory_markdown_files(project_root, memory_dir):
        try:
            chunks.append(file_path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError):
            continue
    return "\n".join(chunks).lower()


def _extract_entities(
    text: str,
    *,
    stopwords: set[str] | frozenset[str],
    verbish: set[str] | frozenset[str],
) -> list[tuple[str, str]]:
    entities: list[tuple[str, str]] = []
    seen: set[str] = set()

    for token in ACRONYM_RE.findall(text):
        if token in stopwords:
            continue
        key = f"acronym:{token.lower()}"
        if key in seen:
            continue
        seen.add(key)
        entities.append((token, "acronym"))

    for phrase in NAME_RE.findall(text):
        if phrase in stopwords:
            continue
        phrase_words = phrase.split()
        if len(phrase_words) == 1 and phrase_words[0].lower() in verbish:
            continue
        key = f"name:{phrase.lower()}"
        if key in seen:
            continue
        seen.add(key)
        entities.append((phrase, "name"))

    return entities


def _detect_memory_gaps(
    local_tasks: list[TaskRecord],
    memory_corpus: str,
    *,
    update_config: ProductivityUpdateConfig,
) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    seen_entities: set[str] = set()

    for task in local_tasks:
        if task.checked:
            continue
        for entity, kind in _extract_entities(
            task.body,
            stopwords=update_config.common_entity_stopwords,
            verbish=update_config.common_entity_verbish,
        ):
            normalized = entity.lower()
            if len(normalized) < 3 or normalized in seen_entities:
                continue
            if normalized in memory_corpus:
                continue
            seen_entities.add(normalized)
            target = "memory/glossary.md" if kind == "acronym" else "memory/projects/"
            confidence = 0.92 if kind == "acronym" else 0.72
            findings.append(
                {
                    "entity": entity,
                    "kind": kind,
                    "sample_task": task.title,
                    "line_number": task.line_number,
                    "target_hint": target,
                    "confidence": confidence,
                }
            )

    findings.sort(key=lambda item: (-float(item["confidence"]), str(item["entity"]).lower()))
    return findings


def _detect_memory_enrichment(local_tasks: list[TaskRecord], memory_corpus: str) -> list[dict[str, Any]]:
    enrichments: list[dict[str, Any]] = []
    seen_urls: set[str] = set()

    for task in local_tasks:
        if task.checked:
            continue
        for url in URL_RE.findall(task.body):
            normalized = url.lower()
            if normalized in seen_urls:
                continue
            seen_urls.add(normalized)
            if normalized in memory_corpus:
                continue
            enrichments.append(
                {
                    "kind": "link",
                    "value": url,
                    "sample_task": task.title,
                    "line_number": task.line_number,
                    "target_hint": "memory/projects/",
                    "confidence": 0.78,
                }
            )
    return enrichments


def _iter_comprehensive_files(project_root: Path) -> Iterable[Path]:
    root_str = str(project_root)
    for current_root, dirnames, filenames in os.walk(root_str):
        dirnames[:] = sorted(
            directory for directory in dirnames if directory not in COMPREHENSIVE_SKIP_DIRS
        )
        for filename in sorted(filenames):
            if not filename.lower().endswith(".md"):
                continue
            candidate = Path(current_root) / filename
            try:
                candidate.relative_to(project_root)
            except ValueError:
                continue
            yield candidate


def _candidate_title_from_todo_line(line: str) -> str:
    cleaned = line.strip()
    cleaned = re.sub(r"^\s*[-*0-9.\)\]]+\s*", "", cleaned)
    cleaned = re.sub(r"(?i)\b(todo|fixme|action item|action:|follow[- ]up)\b[:\-\s]*", "", cleaned)
    cleaned = _strip_task_markup(cleaned).strip(" -:\t")
    if len(cleaned) > 180:
        cleaned = cleaned[:177] + "..."
    return cleaned


def _run_comprehensive_scan(
    *,
    project_root: Path,
    local_tasks: list[TaskRecord],
    memory_corpus: str,
    update_config: ProductivityUpdateConfig,
) -> dict[str, Any]:
    existing_norms = {_normalize_title(task.title) for task in local_tasks if task.title.strip()}
    candidate_tasks: list[dict[str, Any]] = []
    candidate_memory_freq: dict[tuple[str, str], int] = {}
    scanned_files: list[str] = []
    seen_candidate_norms: set[str] = set()

    for file_path in _iter_comprehensive_files(project_root):
        if len(scanned_files) >= update_config.max_comprehensive_scan_files:
            break

        try:
            if file_path.stat().st_size > update_config.max_comprehensive_scan_file_bytes:
                continue
            relative = file_path.relative_to(project_root).as_posix()
            scanned_files.append(relative)
            with file_path.open("r", encoding="utf-8") as handle:
                for line_number, raw_line in enumerate(handle, start=1):
                    line = raw_line.rstrip("\n")
                    if TODO_HINT_RE.search(line):
                        title = _candidate_title_from_todo_line(line)
                        normalized = _normalize_title(title)
                        if not normalized:
                            continue
                        if normalized in existing_norms or normalized in seen_candidate_norms:
                            continue
                        seen_candidate_norms.add(normalized)
                        candidate_tasks.append(
                            {
                                "title": title,
                                "source": f"{relative}:{line_number}",
                                "confidence": 0.64,
                                "kind": "todo_signal",
                            }
                        )

                    for entity, kind in _extract_entities(
                        line,
                        stopwords=update_config.common_entity_stopwords,
                        verbish=update_config.common_entity_verbish,
                    ):
                        normalized_entity = entity.lower()
                        if len(normalized_entity) < 3:
                            continue
                        if normalized_entity in memory_corpus:
                            continue
                        key = (entity, kind)
                        candidate_memory_freq[key] = candidate_memory_freq.get(key, 0) + 1
        except (OSError, UnicodeDecodeError):
            continue

    candidate_memory: list[dict[str, Any]] = []
    for (entity, kind), frequency in sorted(candidate_memory_freq.items(), key=lambda item: (-item[1], item[0][0].lower())):
        if kind != "acronym" and frequency < 2:
            continue
        confidence = min(0.95, 0.58 + (frequency * 0.08))
        candidate_memory.append(
            {
                "entity": entity,
                "kind": kind,
                "frequency": frequency,
                "confidence": round(confidence, 2),
                "target_hint": "memory/glossary.md" if kind == "acronym" else "memory/projects/",
            }
        )

    return {
        "scanned_files": scanned_files,
        "candidate_tasks": candidate_tasks,
        "candidate_memory": candidate_memory,
    }


def _sanitize_markdown_inline(value: Any) -> str:
    text = str(value).strip()
    if not text:
        return ""
    text = " ".join(text.split())
    text = re.sub(r"([\\|`*_\[\]])", r"\\\1", text)
    return text


def _insert_tasks_into_active(tasks_path: Path, additions: list[dict[str, Any]]) -> list[str]:
    if not additions:
        return []

    lines = tasks_path.read_text(encoding="utf-8").splitlines()
    if not lines:
        lines = DEFAULT_TASKS_TEMPLATE.strip("\n").splitlines()

    active_index = next((index for index, line in enumerate(lines) if line.strip() == "## Active"), -1)
    if active_index < 0:
        if lines and lines[-1].strip():
            lines.append("")
        lines.extend(["## Active", ""])
        active_index = len(lines) - 2

    insert_at = active_index + 1
    while insert_at < len(lines) and not re.match(r"^\s*##\s+", lines[insert_at]):
        insert_at += 1

    inserted_titles: list[str] = []
    new_lines: list[str] = []
    for addition in additions:
        title = _sanitize_markdown_inline(addition.get("title", ""))
        if not title:
            continue
        source = _sanitize_markdown_inline(addition.get("source", "external")) or "external"
        source_hint = "github" if source.startswith("http") else source
        new_lines.append(f"- [ ] **{title}** - imported ({source_hint})")
        inserted_titles.append(title)

    if not new_lines:
        return []
    if insert_at > active_index + 1 and lines[insert_at - 1].strip():
        new_lines.insert(0, "")
    lines = lines[:insert_at] + new_lines + lines[insert_at:]
    tasks_path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    return inserted_titles


def _append_glossary_candidates(glossary_path: Path, memory_gaps: list[dict[str, Any]]) -> list[str]:
    if not memory_gaps:
        return []

    glossary_path.parent.mkdir(parents=True, exist_ok=True)
    if glossary_path.exists():
        content = glossary_path.read_text(encoding="utf-8")
    else:
        content = "# Glossary\n"

    lines = content.splitlines()
    if "## Intake Candidates" not in content:
        if lines and lines[-1].strip():
            lines.append("")
        lines.extend(["## Intake Candidates", ""])

    corpus_lower = "\n".join(lines).lower()
    inserted: list[str] = []
    for gap in memory_gaps:
        entity = _sanitize_markdown_inline(gap.get("entity", ""))
        if not entity:
            continue
        if entity.lower() in corpus_lower:
            continue
        sample = _sanitize_markdown_inline(gap.get("sample_task", ""))
        lines.append(f"- {entity}: TODO define (captured from task: {sample})")
        inserted.append(entity)
        corpus_lower += f"\n{entity.lower()}"

    if inserted:
        glossary_path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    return inserted


def _should_apply(
    prompt: str,
    *,
    auto_confirm: bool,
    confirmer: Callable[[str], bool] | None,
    notes: list[str] | None = None,
) -> bool:
    if auto_confirm:
        return True
    if confirmer is None:
        return False
    try:
        return bool(confirmer(prompt))
    except Exception as exc:
        if notes is not None:
            notes.append(f"Confirmation handler error: {exc}")
        return False


def run_productivity_update(
    *,
    project_root: Path,
    comprehensive: bool = False,
    apply_changes: bool = False,
    auto_confirm: bool = False,
    sync_github: bool = True,
    stale_days: int | None = None,
    external_tasks: list[str] | None = None,
    external_tasks_file: Path | None = None,
    confirmer: Callable[[str], bool] | None = None,
) -> UpdateOutcome:
    root = project_root.resolve()
    notes: list[str] = []
    mode = "comprehensive" if comprehensive else "default"

    if not root.exists() or not root.is_dir():
        return UpdateOutcome(
            ok=False,
            mode=mode,
            project_root=root,
            tasks_path=None,
            memory_dir=None,
            notes=notes,
            error=f"Project root does not exist: {root}",
        )

    try:
        update_config = load_productivity_update_config(project_root=root)
    except (TypeError, ValueError) as exc:
        return UpdateOutcome(
            ok=False,
            mode=mode,
            project_root=root,
            tasks_path=None,
            memory_dir=None,
            notes=notes,
            error=f"Invalid productivity_update configuration: {exc}",
        )

    effective_stale_days = stale_days if stale_days is not None else update_config.default_stale_age_days
    if effective_stale_days < 1:
        return UpdateOutcome(
            ok=False,
            mode=mode,
            project_root=root,
            tasks_path=None,
            memory_dir=None,
            notes=notes,
            error="stale_days must be a positive integer.",
        )

    try:
        tasks_path, memory_dir = _resolve_update_paths(root, notes)
    except ValueError as exc:
        return UpdateOutcome(
            ok=False,
            mode=mode,
            project_root=root,
            tasks_path=None,
            memory_dir=None,
            notes=notes,
            error=str(exc),
        )

    if not tasks_path.exists() or not memory_dir.exists():
        return UpdateOutcome(
            ok=False,
            mode=mode,
            project_root=root,
            tasks_path=tasks_path,
            memory_dir=memory_dir,
            notes=notes,
            error=(
                "TASKS.md and/or memory directory are missing. "
                "Run 'specify productivity start' first."
            ),
        )
    if not tasks_path.is_file():
        return UpdateOutcome(
            ok=False,
            mode=mode,
            project_root=root,
            tasks_path=tasks_path,
            memory_dir=memory_dir,
            notes=notes,
            error=f"Configured tasks path must point to a file: {tasks_path}",
        )
    if not memory_dir.is_dir():
        return UpdateOutcome(
            ok=False,
            mode=mode,
            project_root=root,
            tasks_path=tasks_path,
            memory_dir=memory_dir,
            notes=notes,
            error=f"Configured memory path must point to a directory: {memory_dir}",
        )

    try:
        local_tasks = _parse_tasks(tasks_path)
    except (OSError, UnicodeDecodeError) as exc:
        return UpdateOutcome(
            ok=False,
            mode=mode,
            project_root=root,
            tasks_path=tasks_path,
            memory_dir=memory_dir,
            notes=notes,
            error=f"Could not read tasks file: {exc}",
        )

    external_records: list[ExternalTaskRecord] = []
    if external_tasks:
        for title in external_tasks:
            record = _coerce_external_task(title, "manual")
            if record:
                external_records.append(record)
    safe_external_tasks_file: Path | None = None
    if external_tasks_file:
        try:
            safe_external_tasks_file = ensure_path_within_project_root(
                root,
                external_tasks_file,
                field_name="external_tasks_file",
            )
        except ValueError as exc:
            return UpdateOutcome(
                ok=False,
                mode=mode,
                project_root=root,
                tasks_path=tasks_path,
                memory_dir=memory_dir,
                notes=notes,
                error=str(exc),
            )
    if safe_external_tasks_file:
        try:
            external_records.extend(_load_external_tasks_from_file(safe_external_tasks_file, notes))
        except ValueError as exc:
            return UpdateOutcome(
                ok=False,
                mode=mode,
                project_root=root,
                tasks_path=tasks_path,
                memory_dir=memory_dir,
                notes=notes,
                error=str(exc),
            )
    if sync_github:
        external_records.extend(_load_external_tasks_from_github(root, notes))

    task_sync = _analyze_task_sync(
        local_tasks=local_tasks,
        external_tasks=external_records,
        fuzzy_match_threshold=update_config.fuzzy_title_match_threshold,
    )
    stale_findings = _analyze_stale_tasks(local_tasks, stale_days=effective_stale_days)
    memory_corpus = _build_memory_corpus(root, memory_dir)
    analysis_tasks = list(local_tasks)
    for addition in task_sync.get("additions", []):
        title = str(addition.get("title", "")).strip()
        if not title:
            continue
        analysis_tasks.append(
            TaskRecord(
                section="Active",
                title=title,
                body=title,
                line_number=0,
                checked=False,
            )
        )

    memory_gaps = _detect_memory_gaps(
        analysis_tasks,
        memory_corpus,
        update_config=update_config,
    )
    memory_enrichment = _detect_memory_enrichment(analysis_tasks, memory_corpus)
    comprehensive_payload: dict[str, Any] | None = None
    if comprehensive:
        comprehensive_payload = _run_comprehensive_scan(
            project_root=root,
            local_tasks=local_tasks,
            memory_corpus=memory_corpus,
            update_config=update_config,
        )

    applied_tasks: list[str] = []
    applied_memory: list[str] = []
    if apply_changes:
        selected_task_additions = [
            item
            for item in task_sync.get("additions", [])
            if _should_apply(
                f"Add task '{item.get('title', '')}' from {item.get('source', 'external')}?",
                auto_confirm=auto_confirm,
                confirmer=confirmer,
                notes=notes,
            )
        ]
        selected_memory_gaps = [
            gap
            for gap in memory_gaps
            if _should_apply(
                f"Add memory placeholder for '{gap.get('entity', '')}'?",
                auto_confirm=auto_confirm,
                confirmer=confirmer,
                notes=notes,
            )
        ]

        if not auto_confirm and confirmer is None:
            notes.append("Apply requested without confirmation handler; no changes were written.")
        else:
            if selected_task_additions:
                applied_tasks = _insert_tasks_into_active(tasks_path, selected_task_additions)
            if selected_memory_gaps:
                applied_memory = _append_glossary_candidates(memory_dir / "glossary.md", selected_memory_gaps)
    else:
        notes.append("Dry-run mode: no files were changed. Re-run with --apply to persist confirmed additions.")

    return UpdateOutcome(
        ok=True,
        mode=mode,
        project_root=root,
        tasks_path=tasks_path,
        memory_dir=memory_dir,
        task_sync=task_sync,
        stale_findings=stale_findings,
        memory_gaps=memory_gaps,
        memory_enrichment=memory_enrichment,
        comprehensive=comprehensive_payload,
        applied={"tasks": applied_tasks, "memory": applied_memory},
        notes=notes,
    )
