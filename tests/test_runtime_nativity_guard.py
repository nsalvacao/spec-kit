"""Guardrails to keep runtime implementation independent from external plugin paths."""

from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).parent.parent
RUNTIME_ROOTS = (
    Path("src/specify_cli"),
    Path("scripts/bash"),
    Path("scripts/powershell"),
    Path("scripts/python"),
    Path("templates/commands"),
    Path(".github/workflows"),
)
FORBIDDEN_EXTERNAL_BASELINE_MARKERS = (
    ".copilot/installed-plugins/nsalvacao-claude-code-plugins",
    "nsalvacao-claude-code-plugins/productivity-cockpit",
    "nsalvacao-claude-code-plugins/strategy-toolkit",
)
TEXT_SUFFIXES = {".py", ".sh", ".ps1", ".md", ".yml", ".yaml", ".json", ".toml"}


def _iter_runtime_files() -> list[Path]:
    runtime_files: list[Path] = []
    for relative_root in RUNTIME_ROOTS:
        absolute_root = REPO_ROOT / relative_root
        if not absolute_root.exists():
            continue
        for candidate in absolute_root.rglob("*"):
            if candidate.is_file() and candidate.suffix.lower() in TEXT_SUFFIXES:
                runtime_files.append(candidate)
    return runtime_files


def test_runtime_files_do_not_reference_external_plugin_paths() -> None:
    offenders: list[str] = []

    for runtime_file in _iter_runtime_files():
        content = runtime_file.read_text(encoding="utf-8")
        for marker in FORBIDDEN_EXTERNAL_BASELINE_MARKERS:
            if marker in content:
                offenders.append(f"{runtime_file.relative_to(REPO_ROOT)} -> {marker}")

    assert offenders == [], (
        "Runtime implementation must remain native to this repository. "
        "External plugin paths are only allowed in private design docs (for baseline reference):\n"
        + "\n".join(offenders)
    )
