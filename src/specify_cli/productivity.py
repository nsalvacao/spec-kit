"""Native productivity start flow (issue #200, A1 scope)."""

from __future__ import annotations

from dataclasses import dataclass, field
import json
import os
from pathlib import Path
import re
import socket
import subprocess
import sys
import time
from typing import Any
from urllib.error import URLError
from urllib.request import Request, urlopen
import webbrowser


CANONICAL_FEATURE_BRANCH_RE = re.compile(r"^(?P<prefix>\d{3})-(?P<slug>[a-z0-9]+(?:-[a-z0-9]+)*)$")
PRODUCTIVITY_SERVICE_NAME = "specify-productivity-cockpit"
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8001
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
    return {
        "name": "Spec Kit Productivity Cockpit",
        "version": "1.0.0",
        "service": {"host": host, "port": port},
        "paths": {"tasks": tasks_path, "tasks_fallback": "TASKS.md", "memory": "memory", "output": "output"},
        "pulse_rules": {"essential_files": ["README.md"], "min_folders": []},
        "ai": {"mode": "cli", "cli": "codex", "args": []},
    }


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


def _launch_bridge_process(project_root: Path, host: str, port: int) -> subprocess.Popen[str]:
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

    try:
        return subprocess.Popen(command, **popen_kwargs)
    finally:
        log_stream.close()


def ensure_bridge_running(project_root: Path, host: str, port: int) -> tuple[bool, bool]:
    if _probe_running_bridge(host, port):
        return True, True

    process = _launch_bridge_process(project_root, host, port)
    start = time.monotonic()
    while time.monotonic() - start < BRIDGE_START_TIMEOUT_SECONDS:
        if _probe_running_bridge(host, port):
            return True, False
        if process.poll() is not None:
            break
        time.sleep(0.2)
    return False, False


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
    port, reused = resolve_runtime_port(host, preferred_port)
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
