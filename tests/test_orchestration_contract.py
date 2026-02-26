"""Tests for programmatic orchestration contract (issue #113)."""

from __future__ import annotations

import pytest

from specify_cli.orchestration_contract import (
    ORCHESTRATION_CONTRACT_VERSION,
    OrchestrationIssueCode,
    build_orchestration_payload,
    normalize_orchestration_payload,
    validate_orchestration_payload,
)
from specify_cli.scope_detection import ScopeDetectionInput, detect_scope
from specify_cli.scope_gate_contract import ScopeGateChannel, build_scope_gate_payload


def _sample_scope_gate_payload():
    detection_result = detect_scope(
        ScopeDetectionInput(
            description="Create onboarding capability with several internal integrations.",
            estimated_timeline_weeks=8,
            expected_work_items=3,
            dependency_count=3,
            integration_surface_count=2,
            domain_count=2,
            cross_team_count=2,
            risk_level="medium",
        )
    )
    return build_scope_gate_payload(detection_result, channel=ScopeGateChannel.API)


def test_build_orchestration_payload_wraps_scope_gate_payload():
    payload = build_orchestration_payload(_sample_scope_gate_payload(), channel=ScopeGateChannel.CLI)
    serialized = payload.to_dict()

    assert serialized["contract_version"] == ORCHESTRATION_CONTRACT_VERSION
    assert serialized["channel"] == "cli"
    assert serialized["scope_gate"]["contract_version"] == "scope-gate-consumption.v1"
    assert serialized["request_id"]
    assert serialized["timestamp"]


def test_normalize_orchestration_payload_accepts_legacy_scope_gate_shape():
    legacy_payload = _sample_scope_gate_payload().to_dict()
    normalized = normalize_orchestration_payload(legacy_payload)
    codes = {issue.code for issue in normalized.contract_issues}

    assert normalized.contract_version == ORCHESTRATION_CONTRACT_VERSION
    assert OrchestrationIssueCode.LEGACY_SCOPE_GATE_PAYLOAD in codes


def test_normalize_orchestration_payload_falls_back_for_invalid_envelope_fields():
    raw = {
        "contract_version": "",
        "request_id": "not-a-uuid",
        "timestamp": "not-iso8601",
        "channel": "unsupported",
        "scope_gate": _sample_scope_gate_payload().to_dict(),
    }
    normalized = normalize_orchestration_payload(raw, strict=False)
    codes = {issue.code for issue in normalized.contract_issues}

    assert normalized.contract_version == ORCHESTRATION_CONTRACT_VERSION
    assert OrchestrationIssueCode.INVALID_FIELD_TYPE in codes
    assert OrchestrationIssueCode.INVALID_FIELD_VALUE in codes


def test_normalize_orchestration_payload_strict_rejects_unsupported_version():
    raw = {
        "contract_version": "orchestration-payload.v999",
        "request_id": "c8d02cd2-c999-4955-8e19-6ccf3074d4f0",
        "timestamp": "2026-02-26T00:00:00Z",
        "channel": "api",
        "scope_gate": _sample_scope_gate_payload().to_dict(),
    }

    with pytest.raises(ValueError, match="Unsupported contract_version"):
        normalize_orchestration_payload(raw, strict=True)


def test_validate_orchestration_payload_returns_structured_issues():
    raw = {
        "contract_version": ORCHESTRATION_CONTRACT_VERSION,
        "scope_gate": _sample_scope_gate_payload().to_dict(),
    }
    issues = validate_orchestration_payload(raw, strict=False)
    issue_codes = {issue["code"] for issue in issues}

    assert "missing_required_field" in issue_codes
