"""Tests for command discoverability — all template commands must appear in the
CLI 'Next Steps' panel shown after ``specify init``.

Regression test for issue #176.
"""

import pathlib

from specify_cli import __file__ as cli_module_path

# Resolve repository root from installed package location
REPO_ROOT = pathlib.Path(cli_module_path).resolve().parent.parent.parent
TEMPLATES_DIR = REPO_ROOT / "templates" / "commands"


def _canonical_commands() -> set[str]:
    """Return the set of command names derived from template files."""
    return {p.stem for p in TEMPLATES_DIR.glob("*.md")}


def _next_steps_lines() -> str:
    """Extract the 'Next Steps' panel source lines from __init__.py."""
    init_py = REPO_ROOT / "src" / "specify_cli" / "__init__.py"
    return init_py.read_text(encoding="utf-8")


def test_all_template_commands_in_next_steps_panel():
    """Every template command must be referenced in the Next Steps panel."""
    commands = _canonical_commands()
    source = _next_steps_lines()

    missing = []
    for cmd in sorted(commands):
        token = f"/speckit.{cmd}"
        if token not in source:
            missing.append(token)

    assert not missing, (
        f"Commands present in templates/commands/ but missing from the "
        f"'Next Steps' panel in __init__.py: {missing}"
    )


def test_next_steps_panel_has_no_orphan_commands():
    """The Next Steps panel must not reference commands without templates."""
    commands = _canonical_commands()
    source = _next_steps_lines()

    import re

    panel_refs = set(re.findall(r"/speckit\.([a-zA-Z0-9_-]+)", source))
    orphans = panel_refs - commands

    assert not orphans, (
        f"Commands referenced in Next Steps panel but missing from "
        f"templates/commands/: {orphans}"
    )
