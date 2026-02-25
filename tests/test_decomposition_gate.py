"""Tests for decomposition gate flow (issue #106)."""

import pytest

from specify_cli.decomposition_gate import (
    DecompositionGateDecisionOption,
    DecompositionGateState,
    resolve_decomposition_gate,
)
from specify_cli.scope_detection import ScopeDetectionInput, ScopeMode, detect_scope


def _epic_detection_result():
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


def test_follow_recommendation_path_returns_handoff_ready_payload():
    result = resolve_decomposition_gate(
        _epic_detection_result(),
        decision_option=DecompositionGateDecisionOption.FOLLOW,
    )

    assert result.gate_payload.mode_recommendation == ScopeMode.EPIC
    assert result.gate_payload.user_choice == ScopeMode.EPIC
    assert result.gate_payload.override_flag is False
    assert result.state_trace[-1] == DecompositionGateState.HANDOFF_READY


def test_inspect_rationale_path_keeps_recommendation_without_override():
    result = resolve_decomposition_gate(
        _epic_detection_result(),
        decision_option=DecompositionGateDecisionOption.INSPECT_RATIONALE,
    )

    assert result.gate_payload.mode_recommendation == ScopeMode.EPIC
    assert result.gate_payload.user_choice == ScopeMode.EPIC
    assert result.gate_payload.override_flag is False
    assert result.decision_option == DecompositionGateDecisionOption.INSPECT_RATIONALE


def test_override_requires_non_empty_rationale():
    with pytest.raises(ValueError, match="override_rationale is required"):
        resolve_decomposition_gate(
            _epic_detection_result(),
            decision_option=DecompositionGateDecisionOption.OVERRIDE,
            override_mode=ScopeMode.FEATURE,
            risk_acknowledged=True,
            override_rationale="",
        )


def test_override_requires_risk_acknowledgment_for_epic_or_program():
    with pytest.raises(ValueError, match="risk_acknowledged is required"):
        resolve_decomposition_gate(
            _epic_detection_result(),
            decision_option=DecompositionGateDecisionOption.OVERRIDE,
            override_mode=ScopeMode.FEATURE,
            override_rationale="Emergency patch with bounded blast radius.",
            risk_acknowledged=False,
        )


def test_override_requires_different_mode_than_recommendation():
    with pytest.raises(ValueError, match="must differ from mode_recommendation"):
        resolve_decomposition_gate(
            _epic_detection_result(),
            decision_option=DecompositionGateDecisionOption.OVERRIDE,
            override_mode=ScopeMode.EPIC,
            override_rationale="Attempting no-op override",
            risk_acknowledged=True,
        )


def test_override_valid_path_captures_rationale_and_acknowledgment():
    result = resolve_decomposition_gate(
        _epic_detection_result(),
        decision_option=DecompositionGateDecisionOption.OVERRIDE,
        override_mode=ScopeMode.FEATURE,
        override_rationale="Need a narrow emergency patch before broad decomposition.",
        risk_acknowledged=True,
    )

    assert result.gate_payload.override_flag is True
    assert result.gate_payload.user_choice == ScopeMode.FEATURE
    assert result.gate_payload.override_rationale == "Need a narrow emergency patch before broad decomposition."
    assert result.risk_acknowledged is True
    assert result.state_trace == [
        DecompositionGateState.DETECTED,
        DecompositionGateState.RECOMMENDED,
        DecompositionGateState.CHOICE_CAPTURED,
        DecompositionGateState.CONFIRMED,
        DecompositionGateState.HANDOFF_READY,
    ]


def test_invalid_decision_option_is_rejected():
    with pytest.raises(ValueError, match="decision_option must be one of"):
        resolve_decomposition_gate(_epic_detection_result(), decision_option="invalid-option")

