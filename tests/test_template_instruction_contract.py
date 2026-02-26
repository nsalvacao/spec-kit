"""Tests for template/script instruction contract (issue #115)."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from specify_cli.template_instruction_contract import validate_instruction_contract


REPO_ROOT = Path(__file__).parent.parent
SCRIPT = REPO_ROOT / "scripts" / "python" / "template-instruction-contract.py"


def run_script(*args: str, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        cwd=str(cwd) if cwd else None,
        capture_output=True,
        text=True,
    )


def test_instruction_contract_passes_for_repo_templates() -> None:
    errors = validate_instruction_contract(REPO_ROOT)
    assert errors == []


def test_instruction_contract_detects_missing_marker(tmp_path: Path) -> None:
    template = tmp_path / "templates" / "commands" / "specify.md"
    template.parent.mkdir(parents=True, exist_ok=True)
    template.write_text(
        "# Missing required markers\n",
        encoding="utf-8",
    )

    errors = validate_instruction_contract(
        tmp_path,
        template_paths=("templates/commands/specify.md",),
        required_markers=("instruction-contract:options", "instruction-contract:recommended-default"),
    )
    assert len(errors) == 1
    assert errors[0].missing_markers == [
        "instruction-contract:options",
        "instruction-contract:recommended-default",
    ]


def test_template_instruction_contract_script_validate_succeeds() -> None:
    result = run_script("validate", "--repo-root", str(REPO_ROOT))
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["ok"] is True
    assert payload["errors"] == []
