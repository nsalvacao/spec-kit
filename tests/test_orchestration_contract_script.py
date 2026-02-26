"""Tests for orchestration contract helper script (issue #113)."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from specify_cli.scope_detection import ScopeDetectionInput, detect_scope
from specify_cli.scope_gate_contract import ScopeGateChannel, build_scope_gate_payload


SCRIPT = Path(__file__).parent.parent / "scripts" / "python" / "orchestration-contract.py"


def run_script(*args: str, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        cwd=str(cwd) if cwd else None,
        capture_output=True,
        text=True,
    )


def _scope_gate_payload() -> dict[str, object]:
    result = detect_scope(
        ScopeDetectionInput(
            description="Deliver cross-team onboarding and provisioning platform updates.",
            estimated_timeline_weeks=9,
            expected_work_items=4,
            dependency_count=3,
            integration_surface_count=3,
            domain_count=3,
            cross_team_count=2,
            risk_level="high",
        )
    )
    return build_scope_gate_payload(result, channel=ScopeGateChannel.API).to_dict()


def test_orchestration_script_build_wraps_scope_gate_payload(tmp_path: Path) -> None:
    scope_gate_file = tmp_path / "scope-gate.json"
    scope_gate_file.write_text(json.dumps(_scope_gate_payload()), encoding="utf-8")

    result = run_script("build", "--scope-gate", str(scope_gate_file), "--channel", "cli")
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["contract_version"] == "orchestration-payload.v1"
    assert payload["channel"] == "cli"
    assert payload["scope_gate"]["contract_version"] == "scope-gate-consumption.v1"


def test_orchestration_script_validate_fails_invalid_envelope(tmp_path: Path) -> None:
    payload_file = tmp_path / "orchestration.json"
    payload_file.write_text(
        json.dumps(
            {
                "contract_version": "orchestration-payload.v1",
                "request_id": "invalid",
                "timestamp": "invalid",
                "channel": "api",
                "scope_gate": _scope_gate_payload(),
            }
        ),
        encoding="utf-8",
    )

    result = run_script("validate", "--input", str(payload_file))
    assert result.returncode == 1
    payload = json.loads(result.stdout)
    assert payload["ok"] is False
    assert payload["issue_count"] >= 1
