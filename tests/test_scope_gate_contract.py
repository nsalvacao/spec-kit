"""Tests for scope gate consumption contract (issue #105)."""

import pytest

from specify_cli.scope_detection import ScopeDetectionInput, ScopeMode, detect_scope
from specify_cli.scope_gate_contract import (
    SCOPE_GATE_CONTRACT_VERSION,
    ScopeGateErrorCode,
    ScopeGateIssueSeverity,
    ScopeGatePayload,
    build_scope_gate_payload,
    normalize_scope_gate_payload,
    validate_scope_gate_payload,
)


def _sample_epic_detection_result():
    return detect_scope(
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


def test_build_scope_gate_payload_defaults_to_recommendation_choice():
    detection_result = _sample_epic_detection_result()
    payload = build_scope_gate_payload(detection_result)

    assert payload.contract_version == SCOPE_GATE_CONTRACT_VERSION
    assert payload.mode_recommendation == ScopeMode.EPIC
    assert payload.user_choice == payload.mode_recommendation
    assert payload.override_flag is False
    assert payload.next_action == "Decompose epic into features before generating tasks."
    assert payload.handoff_owner == "human:planner"
    assert payload.validation_status.status == "pass"
    assert payload.contract_issues == []


def test_build_scope_gate_payload_supports_explicit_override():
    detection_result = _sample_epic_detection_result()
    payload = build_scope_gate_payload(
        detection_result,
        user_choice="feature",
        override_rationale="Need an emergency single-feature patch first.",
    )

    assert payload.mode_recommendation == ScopeMode.EPIC
    assert payload.user_choice == ScopeMode.FEATURE
    assert payload.override_flag is True
    assert payload.override_rationale == "Need an emergency single-feature patch first."
    assert payload.next_action == "Proceed with feature-level task generation."
    assert payload.handoff_owner == "agent:tasks"


def test_normalize_scope_gate_payload_applies_fallbacks():
    raw = {
        "mode_recommendation": "epic",
        "recommendation_reasons": ["Cross-team dependencies are moderate.", "Multiple integrations are required."],
    }
    payload = normalize_scope_gate_payload(raw)

    assert payload.user_choice == ScopeMode.EPIC
    assert payload.override_flag is False
    assert payload.next_action == "Decompose epic into features before generating tasks."
    assert payload.handoff_owner == "human:planner"
    assert payload.artifacts_created == []
    codes = {issue.code for issue in payload.contract_issues}
    assert ScopeGateErrorCode.MISSING_REQUIRED_FIELD in codes


def test_normalize_scope_gate_payload_strict_mode_rejects_invalid_recommendation():
    raw = {
        "mode_recommendation": "invalid-mode",
        "recommendation_reasons": ["Reason one.", "Reason two."],
    }

    with pytest.raises(ValueError, match="mode_recommendation"):
        normalize_scope_gate_payload(raw, strict=True)


def test_validate_scope_gate_payload_strict_rejects_unknown_fields():
    payload = build_scope_gate_payload(_sample_epic_detection_result()).to_dict()
    payload["unexpected_field"] = "value"

    with pytest.raises(ValueError, match="Unknown contract fields"):
        validate_scope_gate_payload(payload, strict=True)


def test_validate_scope_gate_payload_non_strict_allows_unknown_fields():
    payload = build_scope_gate_payload(_sample_epic_detection_result()).to_dict()
    payload["unexpected_field"] = "value"

    issues = validate_scope_gate_payload(payload, strict=False)
    assert isinstance(issues, list)


def test_normalize_scope_gate_payload_drops_invalid_artifact_entries():
    payload = build_scope_gate_payload(_sample_epic_detection_result()).to_dict()
    payload["artifacts_created"] = ["specs/001/tasks.md", "", 123]

    normalized = normalize_scope_gate_payload(payload)
    assert normalized.artifacts_created == ["specs/001/tasks.md"]
    assert any(issue.code == ScopeGateErrorCode.INVALID_ARTIFACT_PATH for issue in normalized.contract_issues)


def test_normalize_scope_gate_payload_includes_required_contract_fields():
    payload = build_scope_gate_payload(_sample_epic_detection_result())
    serialized = payload.to_dict()

    for field_name in (
        "mode_recommendation",
        "recommendation_reasons",
        "user_choice",
        "override_flag",
        "next_action",
        "handoff_owner",
        "artifacts_created",
        "validation_status",
    ):
        assert field_name in serialized


def test_normalize_scope_gate_payload_marks_fail_on_error_issues():
    raw = {
        "mode_recommendation": "invalid-mode",
        "recommendation_reasons": ["Reason one.", "Reason two."],
        "validation_status": None,
    }
    payload = normalize_scope_gate_payload(raw, strict=False)

    assert payload.validation_status.status == "fail"
    assert any(issue.severity == ScopeGateIssueSeverity.ERROR for issue in payload.contract_issues)


def test_build_scope_gate_payload_returns_typed_payload_object():
    payload = build_scope_gate_payload(_sample_epic_detection_result())
    assert isinstance(payload, ScopeGatePayload)
