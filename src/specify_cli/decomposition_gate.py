"""Decomposition gate flow with explicit override/risk controls.

This module implements the mandatory decision flow between scope detection and
task generation:

detect -> recommend -> choose -> confirm -> handoff
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Mapping

from .scope_detection import ScopeDetectionInput, ScopeDetectionResult, ScopeMode, detect_scope_for_project
from .scope_gate_contract import ScopeGateChannel, ScopeGatePayload, build_scope_gate_payload


DECOMPOSITION_GATE_FLOW_VERSION = "decomposition-gate-flow.v1"


class DecompositionGateState(str, Enum):
    """Canonical state sequence for gate decision flow."""

    DETECTED = "detected"
    RECOMMENDED = "recommended"
    CHOICE_CAPTURED = "choice_captured"
    CONFIRMED = "confirmed"
    HANDOFF_READY = "handoff_ready"


class DecompositionGateDecisionOption(str, Enum):
    """Supported user options at decision checkpoint."""

    FOLLOW = "follow"
    INSPECT_RATIONALE = "inspect_rationale"
    OVERRIDE = "override"


@dataclass(frozen=True)
class DecompositionGateResult:
    """Structured decomposition gate output including state trace and payload."""

    flow_version: str
    decision_option: DecompositionGateDecisionOption
    state_trace: list[DecompositionGateState]
    risk_acknowledged: bool
    gate_payload: ScopeGatePayload

    def to_dict(self) -> dict[str, Any]:
        return {
            "flow_version": self.flow_version,
            "decision_option": self.decision_option.value,
            "state_trace": [state.value for state in self.state_trace],
            "risk_acknowledged": self.risk_acknowledged,
            "scope_gate": self.gate_payload.to_dict(),
        }


def resolve_decomposition_gate(
    detection_result: ScopeDetectionResult,
    *,
    decision_option: DecompositionGateDecisionOption | str,
    override_mode: ScopeMode | str | None = None,
    override_rationale: str | None = None,
    risk_acknowledged: bool = False,
    artifacts_created: list[str] | None = None,
    channel: ScopeGateChannel | str = ScopeGateChannel.CLI,
) -> DecompositionGateResult:
    """Resolve mandatory decomposition gate and produce handoff payload."""
    if not isinstance(detection_result, ScopeDetectionResult):
        raise TypeError("detection_result must be ScopeDetectionResult")

    option = _coerce_decision_option(decision_option)
    state_trace: list[DecompositionGateState] = [DecompositionGateState.DETECTED, DecompositionGateState.RECOMMENDED]

    recommended_mode = detection_result.mode_recommendation
    user_choice = recommended_mode
    normalized_rationale = None
    risk_ack_required = False

    if option == DecompositionGateDecisionOption.OVERRIDE:
        user_choice = _coerce_scope_mode(override_mode, field_name="override_mode")
        if user_choice == recommended_mode:
            raise ValueError("override_mode must differ from mode_recommendation")

        normalized_rationale = _normalize_non_empty_rationale(override_rationale)
        risk_ack_required = recommended_mode in {ScopeMode.EPIC, ScopeMode.PROGRAM}
        if risk_ack_required and not risk_acknowledged:
            raise ValueError("risk_acknowledged is required when overriding epic/program recommendation")
    elif option in {DecompositionGateDecisionOption.FOLLOW, DecompositionGateDecisionOption.INSPECT_RATIONALE}:
        # For follow/inspect flows, selected mode stays aligned with recommendation.
        user_choice = recommended_mode
        risk_acknowledged = False

    state_trace.append(DecompositionGateState.CHOICE_CAPTURED)
    state_trace.append(DecompositionGateState.CONFIRMED)

    gate_payload = build_scope_gate_payload(
        detection_result,
        user_choice=user_choice,
        override_rationale=normalized_rationale,
        artifacts_created=artifacts_created,
        channel=channel,
    )

    state_trace.append(DecompositionGateState.HANDOFF_READY)
    return DecompositionGateResult(
        flow_version=DECOMPOSITION_GATE_FLOW_VERSION,
        decision_option=option,
        state_trace=state_trace,
        risk_acknowledged=risk_acknowledged if risk_ack_required else False,
        gate_payload=gate_payload,
    )


def run_decomposition_gate_for_input(
    input_data: ScopeDetectionInput,
    *,
    decision_option: DecompositionGateDecisionOption | str,
    project_root: Path | None = None,
    env: Mapping[str, str] | None = None,
    override_mode: ScopeMode | str | None = None,
    override_rationale: str | None = None,
    risk_acknowledged: bool = False,
    artifacts_created: list[str] | None = None,
    channel: ScopeGateChannel | str = ScopeGateChannel.CLI,
) -> DecompositionGateResult:
    """Detect initiative scope and run decomposition gate flow."""
    detection_result = detect_scope_for_project(input_data, project_root=project_root, env=env)
    return resolve_decomposition_gate(
        detection_result,
        decision_option=decision_option,
        override_mode=override_mode,
        override_rationale=override_rationale,
        risk_acknowledged=risk_acknowledged,
        artifacts_created=artifacts_created,
        channel=channel,
    )


def _coerce_decision_option(value: DecompositionGateDecisionOption | str) -> DecompositionGateDecisionOption:
    if isinstance(value, DecompositionGateDecisionOption):
        return value
    if isinstance(value, str):
        normalized = value.strip().lower()
        for option in DecompositionGateDecisionOption:
            if normalized == option.value:
                return option
    allowed = ", ".join(option.value for option in DecompositionGateDecisionOption)
    raise ValueError(f"decision_option must be one of: {allowed}")


def _coerce_scope_mode(value: ScopeMode | str | None, *, field_name: str) -> ScopeMode:
    if isinstance(value, ScopeMode):
        return value
    if isinstance(value, str):
        normalized = value.strip().lower()
        for mode in ScopeMode:
            if normalized == mode.value:
                return mode
    raise ValueError(f"{field_name} must be one of: feature, epic, program")


def _normalize_non_empty_rationale(value: str | None) -> str:
    if isinstance(value, str) and value.strip():
        return value.strip()
    raise ValueError("override_rationale is required when overriding recommendation")
