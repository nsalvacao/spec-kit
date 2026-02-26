"""Tests for handoff metadata schema and lint gate (issue #116)."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from specify_cli.handoff_contract import (
    HANDOFF_CONTRACT_VERSION,
    HandoffIssueCode,
    build_handoff_metadata,
    normalize_handoff_metadata,
)
from specify_cli.handoff_metadata_lint import (
    validate_payload_file,
    validate_template_handoffs,
)


REPO_ROOT = Path(__file__).parent.parent
SCRIPT = REPO_ROOT / "scripts" / "python" / "handoff-metadata-lint.py"


def run_script(*args: str, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        cwd=str(cwd) if cwd else None,
        capture_output=True,
        text=True,
    )


def test_build_handoff_metadata_creates_valid_payload() -> None:
    payload = build_handoff_metadata(
        from_stage="specify",
        to_stage="plan",
        handoff_owner="agent:planner",
        next_action="Generate implementation plan.",
    )
    serialized = payload.to_dict()

    assert serialized["contract_version"] == HANDOFF_CONTRACT_VERSION
    assert serialized["validation_status"]["status"] == "pass"
    assert serialized["contract_issues"] == []


def test_build_handoff_metadata_sdd_to_specify_transition() -> None:
    payload = build_handoff_metadata(
        from_stage="sdd",
        to_stage="specify",
        handoff_owner="agent:specify",
        next_action="Create feature specification from validated vision brief.",
    )
    serialized = payload.to_dict()

    assert serialized["from_stage"] == "sdd"
    assert serialized["to_stage"] == "specify"
    assert serialized["validation_status"]["status"] == "pass"
    assert serialized["contract_issues"] == []


def test_normalize_handoff_metadata_reports_invalid_transition() -> None:
    normalized = normalize_handoff_metadata(
        {
            "contract_version": HANDOFF_CONTRACT_VERSION,
            "from_stage": "specify",
            "to_stage": "implement",
            "handoff_owner": "agent:implementer",
            "next_action": "Skip plan and run implementation.",
            "timestamp": "2026-02-26T00:00:00Z",
            "validation_status": {"status": "pass", "blocking_reasons": [], "warnings": []},
        },
        strict=False,
    )
    codes = {issue.code for issue in normalized.contract_issues}

    assert HandoffIssueCode.INVALID_STAGE_TRANSITION in codes
    assert normalized.validation_status.status == "fail"
    assert normalized.validation_status.blocking_reasons


def test_normalize_handoff_metadata_strict_rejects_invalid_transition() -> None:
    with pytest.raises(ValueError, match="Invalid stage transition"):
        normalize_handoff_metadata(
            {
                "contract_version": HANDOFF_CONTRACT_VERSION,
                "from_stage": "specify",
                "to_stage": "implement",
                "handoff_owner": "agent:implementer",
                "next_action": "Skip plan and run implementation.",
                "timestamp": "2026-02-26T00:00:00Z",
                "validation_status": {"status": "pass", "blocking_reasons": [], "warnings": []},
            },
            strict=True,
        )


def test_normalize_handoff_metadata_flags_unsupported_contract_version() -> None:
    normalized = normalize_handoff_metadata(
        {
            "contract_version": "handoff-metadata.v9",
            "from_stage": "specify",
            "to_stage": "plan",
            "handoff_owner": "agent:planner",
            "next_action": "Build technical plan.",
            "timestamp": "2026-02-26T00:00:00Z",
            "validation_status": {"status": "pass", "blocking_reasons": [], "warnings": []},
        },
        strict=False,
    )
    codes = {issue.code for issue in normalized.contract_issues}
    assert HandoffIssueCode.UNSUPPORTED_CONTRACT_VERSION in codes


def test_validate_template_handoffs_passes_repo_templates() -> None:
    errors = validate_template_handoffs(REPO_ROOT)
    assert errors == []


def test_validate_payload_file_returns_nonzero_for_invalid_payload(tmp_path: Path) -> None:
    payload_file = tmp_path / "handoff.json"
    payload_file.write_text(
        json.dumps(
            {
                "from_stage": "specify",
                "to_stage": "implement",
                "handoff_owner": "agent:impl",
                "next_action": "Skip planning.",
            }
        ),
        encoding="utf-8",
    )

    normalized, exit_code = validate_payload_file(payload_file, strict=False)
    assert exit_code == 1
    assert normalized["validation_status"]["status"] == "fail"


def test_handoff_metadata_lint_script_templates_succeeds() -> None:
    result = run_script("templates", "--repo-root", str(REPO_ROOT))
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["ok"] is True


def test_handoff_metadata_lint_script_payload_fails_invalid_transition(tmp_path: Path) -> None:
    payload_file = tmp_path / "handoff.json"
    payload_file.write_text(
        json.dumps(
            {
                "contract_version": HANDOFF_CONTRACT_VERSION,
                "from_stage": "specify",
                "to_stage": "implement",
                "handoff_owner": "agent:impl",
                "next_action": "Skip planning.",
                "timestamp": "2026-02-26T00:00:00Z",
                "validation_status": {"status": "pass", "blocking_reasons": [], "warnings": []},
            }
        ),
        encoding="utf-8",
    )
    result = run_script("payload", "--input", str(payload_file))
    assert result.returncode == 1
    payload = json.loads(result.stdout)
    assert payload["ok"] is False


def test_handoff_metadata_lint_script_payload_rejects_oversized_input(tmp_path: Path) -> None:
    payload_file = tmp_path / "oversized.json"
    payload_file.write_text(" " * 1_048_577, encoding="utf-8")

    result = run_script("payload", "--input", str(payload_file))
    assert result.returncode == 1
    assert "too large" in result.stderr.lower()


def test_handoff_metadata_lint_script_payload_rejects_excessive_depth(tmp_path: Path) -> None:
    deep_payload: dict[str, object] = {}
    cursor: dict[str, object] = deep_payload
    for _ in range(70):
        nested: dict[str, object] = {}
        cursor["nested"] = nested
        cursor = nested
    payload_file = tmp_path / "too-deep.json"
    payload_file.write_text(json.dumps(deep_payload), encoding="utf-8")

    result = run_script("payload", "--input", str(payload_file))
    assert result.returncode == 1
    assert "nesting depth" in result.stderr.lower()
