"""Stable scope gate consumption contract for CLI/TTY/API channels.

This module defines a channel-agnostic payload contract that wraps scope
detection output with user choice and handoff metadata.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Mapping
from pathlib import PurePosixPath

from .scope_detection import ScopeDetectionResult, ScopeMode


SCOPE_GATE_CONTRACT_VERSION = "scope-gate-consumption.v1"
SCOPE_GATE_REQUIRED_FIELDS = frozenset(
    {
        "mode_recommendation",
        "recommendation_reasons",
        "user_choice",
        "override_flag",
        "next_action",
        "handoff_owner",
        "artifacts_created",
        "validation_status",
    }
)
SCOPE_GATE_ALLOWED_FIELDS = frozenset(
    set(SCOPE_GATE_REQUIRED_FIELDS)
    | {"contract_version", "override_rationale", "channel", "contract_issues"}
)


class ScopeGateChannel(str, Enum):
    """Supported execution channels for the shared contract."""

    CLI = "cli"
    TTY = "tty"
    API = "api"


class ScopeGateIssueSeverity(str, Enum):
    """Severity for contract issues and fallback diagnostics."""

    WARNING = "warning"
    ERROR = "error"


class ScopeGateErrorCode(str, Enum):
    """Known contract validation/fallback issue codes."""

    MISSING_REQUIRED_FIELD = "missing_required_field"
    INVALID_FIELD_TYPE = "invalid_field_type"
    INVALID_FIELD_VALUE = "invalid_field_value"
    INVALID_ARTIFACT_PATH = "invalid_artifact_path"
    UNKNOWN_FIELD = "unknown_field"


@dataclass(frozen=True)
class ScopeGateContractIssue:
    """Structured issue emitted while validating/normalizing payloads."""

    code: ScopeGateErrorCode
    field: str
    message: str
    severity: ScopeGateIssueSeverity = ScopeGateIssueSeverity.WARNING

    def to_dict(self) -> dict[str, str]:
        return {
            "code": self.code.value,
            "field": self.field,
            "message": self.message,
            "severity": self.severity.value,
        }


@dataclass(frozen=True)
class ScopeGateValidationStatus:
    """Validation status embedded in the stable gate payload."""

    status: str
    blocking_reasons: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def validate(self) -> None:
        """Validate validation-status shape and values."""
        normalized_status = self.status.strip().lower()
        if normalized_status not in {"pass", "fail"}:
            raise ValueError("validation_status.status must be 'pass' or 'fail'")
        if not all(isinstance(item, str) for item in self.blocking_reasons):
            raise TypeError("validation_status.blocking_reasons must contain strings")
        if not all(isinstance(item, str) for item in self.warnings):
            raise TypeError("validation_status.warnings must contain strings")

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status.strip().lower(),
            "blocking_reasons": self.blocking_reasons,
            "warnings": self.warnings,
        }


@dataclass(frozen=True)
class ScopeGatePayload:
    """Channel-agnostic contract payload for gate consumers."""

    contract_version: str
    mode_recommendation: ScopeMode
    recommendation_reasons: list[str]
    user_choice: ScopeMode
    override_flag: bool
    next_action: str
    handoff_owner: str
    artifacts_created: list[str]
    validation_status: ScopeGateValidationStatus
    override_rationale: str | None = None
    channel: ScopeGateChannel = ScopeGateChannel.API
    contract_issues: list[ScopeGateContractIssue] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        payload = {
            "contract_version": self.contract_version,
            "mode_recommendation": self.mode_recommendation.value,
            "recommendation_reasons": self.recommendation_reasons,
            "user_choice": self.user_choice.value,
            "override_flag": self.override_flag,
            "next_action": self.next_action,
            "handoff_owner": self.handoff_owner,
            "artifacts_created": self.artifacts_created,
            "validation_status": self.validation_status.to_dict(),
            "channel": self.channel.value,
            "contract_issues": [issue.to_dict() for issue in self.contract_issues],
        }
        if self.override_rationale:
            payload["override_rationale"] = self.override_rationale
        return payload


def build_scope_gate_payload(
    detection_result: ScopeDetectionResult,
    *,
    user_choice: ScopeMode | str | None = None,
    override_rationale: str | None = None,
    next_action: str | None = None,
    handoff_owner: str | None = None,
    artifacts_created: list[str] | None = None,
    channel: ScopeGateChannel | str = ScopeGateChannel.API,
) -> ScopeGatePayload:
    """Build stable gate payload from scope detection output."""
    if not isinstance(detection_result, ScopeDetectionResult):
        raise TypeError("detection_result must be ScopeDetectionResult")

    issues: list[ScopeGateContractIssue] = []
    recommendation = detection_result.mode_recommendation
    normalized_user_choice = _coerce_mode(
        user_choice,
        field_name="user_choice",
        fallback=recommendation,
        issues=issues,
        missing_severity=ScopeGateIssueSeverity.WARNING,
        emit_missing_issue=False,
    )
    override_flag = normalized_user_choice != recommendation
    normalized_override_rationale = (
        override_rationale.strip() if isinstance(override_rationale, str) and override_rationale.strip() else None
    )

    normalized_channel = _coerce_channel(channel, issues=issues)
    normalized_next_action = _coerce_non_empty_string(
        value=next_action,
        field_name="next_action",
        fallback=_derive_next_action(normalized_user_choice),
        issues=issues,
        emit_missing_issue=False,
    )
    normalized_handoff_owner = _coerce_non_empty_string(
        value=handoff_owner,
        field_name="handoff_owner",
        fallback=_derive_handoff_owner(normalized_user_choice),
        issues=issues,
        emit_missing_issue=False,
    )
    normalized_artifacts = _normalize_artifacts(artifacts_created, issues=issues, emit_missing_issue=False)
    normalized_reasons = _normalize_recommendation_reasons(
        detection_result.recommendation_reasons,
        mode_recommendation=recommendation,
        issues=issues,
        source_field="recommendation_reasons",
    )
    validation_status = _build_validation_status(issues=issues)

    return ScopeGatePayload(
        contract_version=SCOPE_GATE_CONTRACT_VERSION,
        mode_recommendation=recommendation,
        recommendation_reasons=normalized_reasons,
        user_choice=normalized_user_choice,
        override_flag=override_flag,
        override_rationale=normalized_override_rationale,
        next_action=normalized_next_action,
        handoff_owner=normalized_handoff_owner,
        artifacts_created=normalized_artifacts,
        validation_status=validation_status,
        channel=normalized_channel,
        contract_issues=issues,
    )


def normalize_scope_gate_payload(
    raw_payload: Mapping[str, Any],
    *,
    strict: bool = False,
) -> ScopeGatePayload:
    """Normalize external channel payload into the stable contract shape.

    Fallback behavior:
    - missing `user_choice` -> defaults to `mode_recommendation`
    - missing `override_flag` -> derived from recommendation vs choice
    - missing `next_action`/`handoff_owner` -> deterministic defaults
    - missing/invalid `validation_status` -> derived from contract issues
    - missing/invalid reasons -> generated conservative fallback reasons
    """
    if not isinstance(raw_payload, Mapping):
        raise TypeError("raw_payload must be a mapping")

    issues: list[ScopeGateContractIssue] = []
    payload_keys = set(raw_payload.keys())
    unknown_keys = sorted(payload_keys - SCOPE_GATE_ALLOWED_FIELDS)
    if unknown_keys and strict:
        unknown = ", ".join(unknown_keys)
        issues.append(
            ScopeGateContractIssue(
                code=ScopeGateErrorCode.UNKNOWN_FIELD,
                field="*",
                message=f"Unknown contract fields: {unknown}",
                severity=ScopeGateIssueSeverity.ERROR,
            )
        )

    recommendation = _coerce_mode(
        raw_payload.get("mode_recommendation"),
        field_name="mode_recommendation",
        fallback=ScopeMode.FEATURE,
        issues=issues,
        missing_severity=ScopeGateIssueSeverity.ERROR,
    )
    normalized_reasons = _normalize_recommendation_reasons(
        raw_payload.get("recommendation_reasons"),
        mode_recommendation=recommendation,
        issues=issues,
        source_field="recommendation_reasons",
    )
    user_choice = _coerce_mode(
        raw_payload.get("user_choice"),
        field_name="user_choice",
        fallback=recommendation,
        issues=issues,
        missing_severity=ScopeGateIssueSeverity.WARNING,
    )

    raw_override_flag = raw_payload.get("override_flag")
    derived_override_flag = user_choice != recommendation
    if raw_override_flag is None:
        issues.append(
            ScopeGateContractIssue(
                code=ScopeGateErrorCode.MISSING_REQUIRED_FIELD,
                field="override_flag",
                message="Missing override_flag; derived from mode_recommendation vs user_choice.",
                severity=ScopeGateIssueSeverity.WARNING,
            )
        )
        override_flag = derived_override_flag
    elif isinstance(raw_override_flag, bool):
        override_flag = raw_override_flag
    else:
        issues.append(
            ScopeGateContractIssue(
                code=ScopeGateErrorCode.INVALID_FIELD_TYPE,
                field="override_flag",
                message="Invalid override_flag; expected boolean. Derived value was applied.",
                severity=ScopeGateIssueSeverity.WARNING,
            )
        )
        override_flag = derived_override_flag

    override_rationale = raw_payload.get("override_rationale")
    if override_rationale is not None and not isinstance(override_rationale, str):
        issues.append(
            ScopeGateContractIssue(
                code=ScopeGateErrorCode.INVALID_FIELD_TYPE,
                field="override_rationale",
                message="Invalid override_rationale; expected string or null.",
                severity=ScopeGateIssueSeverity.WARNING,
            )
        )
        override_rationale = None
    elif isinstance(override_rationale, str):
        override_rationale = override_rationale.strip() or None

    next_action = _coerce_non_empty_string(
        value=raw_payload.get("next_action"),
        field_name="next_action",
        fallback=_derive_next_action(user_choice),
        issues=issues,
    )
    handoff_owner = _coerce_non_empty_string(
        value=raw_payload.get("handoff_owner"),
        field_name="handoff_owner",
        fallback=_derive_handoff_owner(user_choice),
        issues=issues,
    )
    artifacts_created = _normalize_artifacts(raw_payload.get("artifacts_created"), issues=issues)

    channel = _coerce_channel(raw_payload.get("channel", ScopeGateChannel.API.value), issues=issues)
    contract_version = raw_payload.get("contract_version")
    if contract_version is None:
        issues.append(
            ScopeGateContractIssue(
                code=ScopeGateErrorCode.MISSING_REQUIRED_FIELD,
                field="contract_version",
                message=f"Missing contract_version; defaulted to {SCOPE_GATE_CONTRACT_VERSION}.",
                severity=ScopeGateIssueSeverity.WARNING,
            )
        )
        contract_version = SCOPE_GATE_CONTRACT_VERSION
    elif not isinstance(contract_version, str) or not contract_version.strip():
        issues.append(
            ScopeGateContractIssue(
                code=ScopeGateErrorCode.INVALID_FIELD_TYPE,
                field="contract_version",
                message=f"Invalid contract_version; defaulted to {SCOPE_GATE_CONTRACT_VERSION}.",
                severity=ScopeGateIssueSeverity.WARNING,
            )
        )
        contract_version = SCOPE_GATE_CONTRACT_VERSION
    else:
        contract_version = contract_version.strip()

    validation_status = _normalize_validation_status(raw_payload.get("validation_status"), issues=issues)

    payload = ScopeGatePayload(
        contract_version=contract_version,
        mode_recommendation=recommendation,
        recommendation_reasons=normalized_reasons,
        user_choice=user_choice,
        override_flag=override_flag,
        next_action=next_action,
        handoff_owner=handoff_owner,
        artifacts_created=artifacts_created,
        validation_status=validation_status,
        override_rationale=override_rationale,
        channel=channel,
        contract_issues=issues,
    )
    _raise_on_strict_errors(issues=issues, strict=strict)
    return payload


def validate_scope_gate_payload(
    payload: Mapping[str, Any],
    *,
    strict: bool = True,
) -> list[ScopeGateContractIssue]:
    """Validate channel payload and return contract issues.

    In strict mode, raises `ValueError` if any error-severity issue is detected.
    """
    normalized = normalize_scope_gate_payload(payload, strict=False)
    issues = normalized.contract_issues

    if strict:
        payload_keys = set(payload.keys())
        unknown_keys = sorted(payload_keys - SCOPE_GATE_ALLOWED_FIELDS)
        if unknown_keys:
            unknown = ", ".join(unknown_keys)
            issues = [
                *issues,
                ScopeGateContractIssue(
                    code=ScopeGateErrorCode.UNKNOWN_FIELD,
                    field="*",
                    message=f"Unknown contract fields: {unknown}",
                    severity=ScopeGateIssueSeverity.ERROR,
                ),
            ]

    _raise_on_strict_errors(issues=issues, strict=strict)
    return issues


def _coerce_mode(
    value: ScopeMode | str | None,
    *,
    field_name: str,
    fallback: ScopeMode,
    issues: list[ScopeGateContractIssue],
    missing_severity: ScopeGateIssueSeverity,
    emit_missing_issue: bool = True,
) -> ScopeMode:
    if value is None:
        if emit_missing_issue:
            issues.append(
                ScopeGateContractIssue(
                    code=ScopeGateErrorCode.MISSING_REQUIRED_FIELD,
                    field=field_name,
                    message=f"Missing {field_name}; fallback '{fallback.value}' was applied.",
                    severity=missing_severity,
                )
            )
        return fallback

    if isinstance(value, ScopeMode):
        return value

    if isinstance(value, str):
        normalized = value.strip().lower()
        for mode in ScopeMode:
            if normalized == mode.value:
                return mode

    issues.append(
        ScopeGateContractIssue(
            code=ScopeGateErrorCode.INVALID_FIELD_VALUE,
            field=field_name,
            message=f"Invalid {field_name}; fallback '{fallback.value}' was applied.",
            severity=ScopeGateIssueSeverity.ERROR if field_name == "mode_recommendation" else ScopeGateIssueSeverity.WARNING,
        )
    )
    return fallback


def _coerce_non_empty_string(
    *,
    value: Any,
    field_name: str,
    fallback: str,
    issues: list[ScopeGateContractIssue],
    emit_missing_issue: bool = True,
) -> str:
    if isinstance(value, str) and value.strip():
        return value.strip()

    if value is None and not emit_missing_issue:
        return fallback

    issue_code = ScopeGateErrorCode.MISSING_REQUIRED_FIELD if value is None else ScopeGateErrorCode.INVALID_FIELD_TYPE
    issues.append(
        ScopeGateContractIssue(
            code=issue_code,
            field=field_name,
            message=f"Invalid {field_name}; fallback value was applied.",
            severity=ScopeGateIssueSeverity.WARNING,
        )
    )
    return fallback


def _normalize_recommendation_reasons(
    value: Any,
    *,
    mode_recommendation: ScopeMode,
    issues: list[ScopeGateContractIssue],
    source_field: str,
) -> list[str]:
    if isinstance(value, list) and all(isinstance(item, str) and item.strip() for item in value):
        normalized = [item.strip() for item in value]
        if len(normalized) > 3:
            issues.append(
                ScopeGateContractIssue(
                    code=ScopeGateErrorCode.INVALID_FIELD_VALUE,
                    field=source_field,
                    message="recommendation_reasons had more than 3 items; truncated to the first 3.",
                    severity=ScopeGateIssueSeverity.WARNING,
                )
            )
            normalized = normalized[:3]
        if len(normalized) >= 2:
            return normalized

    issue_code = ScopeGateErrorCode.MISSING_REQUIRED_FIELD if value is None else ScopeGateErrorCode.INVALID_FIELD_TYPE
    issues.append(
        ScopeGateContractIssue(
            code=issue_code,
            field=source_field,
            message="Invalid recommendation_reasons; deterministic fallback reasons were applied.",
            severity=ScopeGateIssueSeverity.WARNING,
        )
    )
    return [
        "Producer payload did not provide enough valid rationale details.",
        f"Selected mode '{mode_recommendation.value}' remains the conservative default under limited context.",
    ]


def _normalize_artifacts(
    value: Any,
    *,
    issues: list[ScopeGateContractIssue],
    emit_missing_issue: bool = True,
) -> list[str]:
    if value is None:
        if emit_missing_issue:
            issues.append(
                ScopeGateContractIssue(
                    code=ScopeGateErrorCode.MISSING_REQUIRED_FIELD,
                    field="artifacts_created",
                    message="Missing artifacts_created; defaulted to empty list.",
                    severity=ScopeGateIssueSeverity.WARNING,
                )
            )
        return []

    if not isinstance(value, list):
        issues.append(
            ScopeGateContractIssue(
                code=ScopeGateErrorCode.INVALID_FIELD_TYPE,
                field="artifacts_created",
                message="Invalid artifacts_created; expected list of paths. Defaulted to empty list.",
                severity=ScopeGateIssueSeverity.WARNING,
            )
        )
        return []

    normalized: list[str] = []
    for raw_path in value:
        if not isinstance(raw_path, str):
            issues.append(
                ScopeGateContractIssue(
                    code=ScopeGateErrorCode.INVALID_ARTIFACT_PATH,
                    field="artifacts_created",
                    message="Dropped non-string artifact path entry.",
                    severity=ScopeGateIssueSeverity.WARNING,
                )
            )
            continue
        trimmed = raw_path.strip()
        if not trimmed:
            issues.append(
                ScopeGateContractIssue(
                    code=ScopeGateErrorCode.INVALID_ARTIFACT_PATH,
                    field="artifacts_created",
                    message="Dropped empty artifact path entry.",
                    severity=ScopeGateIssueSeverity.WARNING,
                )
            )
            continue
        path_obj = PurePosixPath(trimmed)
        if path_obj.is_absolute() or any(part == ".." for part in path_obj.parts):
            issues.append(
                ScopeGateContractIssue(
                    code=ScopeGateErrorCode.INVALID_ARTIFACT_PATH,
                    field="artifacts_created",
                    message="Dropped unsafe artifact path (absolute or traversal).",
                    severity=ScopeGateIssueSeverity.ERROR,
                )
            )
            continue
        normalized.append(str(path_obj))
    return normalized


def _coerce_channel(value: Any, *, issues: list[ScopeGateContractIssue]) -> ScopeGateChannel:
    if isinstance(value, ScopeGateChannel):
        return value
    if isinstance(value, str):
        normalized = value.strip().lower()
        for channel in ScopeGateChannel:
            if normalized == channel.value:
                return channel

    issues.append(
        ScopeGateContractIssue(
            code=ScopeGateErrorCode.INVALID_FIELD_VALUE,
            field="channel",
            message=f"Invalid channel; fallback '{ScopeGateChannel.API.value}' was applied.",
            severity=ScopeGateIssueSeverity.WARNING,
        )
    )
    return ScopeGateChannel.API


def _normalize_validation_status(
    value: Any,
    *,
    issues: list[ScopeGateContractIssue],
) -> ScopeGateValidationStatus:
    if value is None:
        issues.append(
            ScopeGateContractIssue(
                code=ScopeGateErrorCode.MISSING_REQUIRED_FIELD,
                field="validation_status",
                message="Missing validation_status; derived from contract issues.",
                severity=ScopeGateIssueSeverity.WARNING,
            )
        )
        return _build_validation_status(issues=issues)

    if not isinstance(value, Mapping):
        issues.append(
            ScopeGateContractIssue(
                code=ScopeGateErrorCode.INVALID_FIELD_TYPE,
                field="validation_status",
                message="Invalid validation_status; derived from contract issues.",
                severity=ScopeGateIssueSeverity.WARNING,
            )
        )
        return _build_validation_status(issues=issues)

    status_value = value.get("status")
    blocking_reasons_value = value.get("blocking_reasons", [])
    warnings_value = value.get("warnings", [])
    if (
        not isinstance(status_value, str)
        or status_value.strip().lower() not in {"pass", "fail"}
        or not isinstance(blocking_reasons_value, list)
        or not isinstance(warnings_value, list)
        or not all(isinstance(item, str) for item in blocking_reasons_value)
        or not all(isinstance(item, str) for item in warnings_value)
    ):
        issues.append(
            ScopeGateContractIssue(
                code=ScopeGateErrorCode.INVALID_FIELD_VALUE,
                field="validation_status",
                message="Invalid validation_status shape; derived from contract issues.",
                severity=ScopeGateIssueSeverity.WARNING,
            )
        )
        return _build_validation_status(issues=issues)

    status = ScopeGateValidationStatus(
        status=status_value.strip().lower(),
        blocking_reasons=[item.strip() for item in blocking_reasons_value],
        warnings=[item.strip() for item in warnings_value],
    )
    status.validate()
    return status


def _build_validation_status(*, issues: list[ScopeGateContractIssue]) -> ScopeGateValidationStatus:
    blocking_reasons = [issue.message for issue in issues if issue.severity == ScopeGateIssueSeverity.ERROR]
    warnings = [issue.message for issue in issues if issue.severity == ScopeGateIssueSeverity.WARNING]
    status = "fail" if blocking_reasons else "pass"
    return ScopeGateValidationStatus(
        status=status,
        blocking_reasons=blocking_reasons,
        warnings=warnings,
    )


def _derive_next_action(mode: ScopeMode) -> str:
    if mode == ScopeMode.FEATURE:
        return "Proceed with feature-level task generation."
    if mode == ScopeMode.EPIC:
        return "Decompose epic into features before generating tasks."
    return "Decompose program into epics and features before generating tasks."


def _derive_handoff_owner(mode: ScopeMode) -> str:
    if mode == ScopeMode.FEATURE:
        return "agent:tasks"
    if mode == ScopeMode.EPIC:
        return "human:planner"
    return "human:program-manager"


def _raise_on_strict_errors(*, issues: list[ScopeGateContractIssue], strict: bool) -> None:
    if not strict:
        return
    errors = [issue for issue in issues if issue.severity == ScopeGateIssueSeverity.ERROR]
    if errors:
        messages = "; ".join(f"{issue.field}: {issue.message}" for issue in errors)
        raise ValueError(f"Scope gate payload validation failed: {messages}")
