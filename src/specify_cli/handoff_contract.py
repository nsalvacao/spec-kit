"""Handoff metadata schema and normalization utilities.

Issue: #116
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Mapping


HANDOFF_CONTRACT_VERSION = "handoff-metadata.v1"
HANDOFF_ALLOWED_CONTRACT_VERSIONS = frozenset({HANDOFF_CONTRACT_VERSION})
HANDOFF_REQUIRED_FIELDS = frozenset(
    {
        "contract_version",
        "from_stage",
        "to_stage",
        "handoff_owner",
        "next_action",
        "timestamp",
        "validation_status",
    }
)
HANDOFF_ALLOWED_STAGES = frozenset(
    (
    "ideate",
    "select",
    "structure",
    "validate",
    "sdd",
    "specify",
    "clarify",
    "plan",
    "tasks",
    "implement",
    )
)
HANDOFF_ALLOWED_TRANSITIONS = frozenset(
    {
        ("ideate", "select"),
        ("select", "structure"),
        ("structure", "validate"),
        ("validate", "sdd"),
        ("specify", "clarify"),
        ("specify", "plan"),
        ("clarify", "plan"),
        ("plan", "tasks"),
        ("tasks", "implement"),
    }
)


class HandoffIssueSeverity(str, Enum):
    WARNING = "warning"
    ERROR = "error"


class HandoffIssueCode(str, Enum):
    MISSING_REQUIRED_FIELD = "missing_required_field"
    INVALID_FIELD_TYPE = "invalid_field_type"
    INVALID_FIELD_VALUE = "invalid_field_value"
    UNSUPPORTED_CONTRACT_VERSION = "unsupported_contract_version"
    INVALID_STAGE_TRANSITION = "invalid_stage_transition"


@dataclass(frozen=True)
class HandoffContractIssue:
    code: HandoffIssueCode
    field: str
    message: str
    severity: HandoffIssueSeverity = HandoffIssueSeverity.WARNING

    def to_dict(self) -> dict[str, str]:
        return {
            "code": self.code.value,
            "field": self.field,
            "message": self.message,
            "severity": self.severity.value,
        }


@dataclass(frozen=True)
class HandoffValidationStatus:
    status: str
    blocking_reasons: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "blocking_reasons": self.blocking_reasons,
            "warnings": self.warnings,
        }


@dataclass(frozen=True)
class HandoffMetadata:
    contract_version: str
    from_stage: str
    to_stage: str
    handoff_owner: str
    next_action: str
    timestamp: str
    validation_status: HandoffValidationStatus
    contract_issues: list[HandoffContractIssue] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "contract_version": self.contract_version,
            "from_stage": self.from_stage,
            "to_stage": self.to_stage,
            "handoff_owner": self.handoff_owner,
            "next_action": self.next_action,
            "timestamp": self.timestamp,
            "validation_status": self.validation_status.to_dict(),
            "contract_issues": [issue.to_dict() for issue in self.contract_issues],
        }


def build_handoff_metadata(
    *,
    from_stage: str,
    to_stage: str,
    handoff_owner: str,
    next_action: str,
    timestamp: str | None = None,
) -> HandoffMetadata:
    """Build strict handoff metadata payload."""
    payload = {
        "contract_version": HANDOFF_CONTRACT_VERSION,
        "from_stage": from_stage,
        "to_stage": to_stage,
        "handoff_owner": handoff_owner,
        "next_action": next_action,
        "timestamp": timestamp or _utc_now(),
        "validation_status": {"status": "pass", "blocking_reasons": [], "warnings": []},
    }
    return normalize_handoff_metadata(payload, strict=True)


def normalize_handoff_metadata(raw_payload: Mapping[str, Any], *, strict: bool = False) -> HandoffMetadata:
    """Normalize handoff metadata payload and return stable schema."""
    if not isinstance(raw_payload, Mapping):
        raise TypeError("raw_payload must be a mapping")

    issues: list[HandoffContractIssue] = []

    contract_version = raw_payload.get("contract_version")
    if contract_version is None:
        issues.append(
            HandoffContractIssue(
                code=HandoffIssueCode.MISSING_REQUIRED_FIELD,
                field="contract_version",
                message=f"Missing contract_version; defaulted to {HANDOFF_CONTRACT_VERSION}.",
            )
        )
        normalized_contract_version = HANDOFF_CONTRACT_VERSION
    elif not isinstance(contract_version, str) or not contract_version.strip():
        issues.append(
            HandoffContractIssue(
                code=HandoffIssueCode.INVALID_FIELD_TYPE,
                field="contract_version",
                message=f"Invalid contract_version; defaulted to {HANDOFF_CONTRACT_VERSION}.",
            )
        )
        normalized_contract_version = HANDOFF_CONTRACT_VERSION
    else:
        normalized_contract_version = contract_version.strip()

    if normalized_contract_version not in HANDOFF_ALLOWED_CONTRACT_VERSIONS:
        issues.append(
            HandoffContractIssue(
                code=HandoffIssueCode.UNSUPPORTED_CONTRACT_VERSION,
                field="contract_version",
                message=(
                    f"Unsupported contract_version '{normalized_contract_version}'. "
                    f"Supported: {sorted(HANDOFF_ALLOWED_CONTRACT_VERSIONS)}."
                ),
                severity=HandoffIssueSeverity.ERROR,
            )
        )
        normalized_contract_version = HANDOFF_CONTRACT_VERSION

    from_stage = _normalize_stage("from_stage", raw_payload.get("from_stage"), issues=issues, fallback="specify")
    to_stage = _normalize_stage("to_stage", raw_payload.get("to_stage"), issues=issues, fallback="plan")

    if (from_stage, to_stage) not in HANDOFF_ALLOWED_TRANSITIONS:
        issues.append(
            HandoffContractIssue(
                code=HandoffIssueCode.INVALID_STAGE_TRANSITION,
                field="to_stage",
                message=f"Invalid stage transition: {from_stage} -> {to_stage}.",
                severity=HandoffIssueSeverity.ERROR,
            )
        )

    handoff_owner = _normalize_handoff_owner(raw_payload.get("handoff_owner"), issues=issues)
    next_action = _normalize_non_empty_string(
        field_name="next_action",
        value=raw_payload.get("next_action"),
        fallback="Review current stage output and proceed to the next stage.",
        issues=issues,
    )
    timestamp = _normalize_timestamp(raw_payload.get("timestamp"), issues=issues)
    validation_status = _normalize_validation_status(raw_payload.get("validation_status"), issues=issues)

    if strict:
        errors = [issue.message for issue in issues if issue.severity == HandoffIssueSeverity.ERROR]
        if errors:
            raise ValueError("; ".join(errors))

    return HandoffMetadata(
        contract_version=normalized_contract_version,
        from_stage=from_stage,
        to_stage=to_stage,
        handoff_owner=handoff_owner,
        next_action=next_action,
        timestamp=timestamp,
        validation_status=validation_status,
        contract_issues=issues,
    )


def validate_handoff_metadata(raw_payload: Mapping[str, Any], *, strict: bool = False) -> list[dict[str, str]]:
    normalized = normalize_handoff_metadata(raw_payload, strict=strict)
    return [issue.to_dict() for issue in normalized.contract_issues]


def _normalize_stage(
    field_name: str,
    value: Any,
    *,
    issues: list[HandoffContractIssue],
    fallback: str,
) -> str:
    if value is None:
        issues.append(
            HandoffContractIssue(
                code=HandoffIssueCode.MISSING_REQUIRED_FIELD,
                field=field_name,
                message=f"Missing {field_name}; defaulted to '{fallback}'.",
            )
        )
        return fallback
    if not isinstance(value, str) or not value.strip():
        issues.append(
            HandoffContractIssue(
                code=HandoffIssueCode.INVALID_FIELD_TYPE,
                field=field_name,
                message=f"Invalid {field_name}; defaulted to '{fallback}'.",
            )
        )
        return fallback
    normalized = value.strip().lower()
    if normalized not in HANDOFF_ALLOWED_STAGES:
        issues.append(
            HandoffContractIssue(
                code=HandoffIssueCode.INVALID_FIELD_VALUE,
                field=field_name,
                message=f"Invalid {field_name}; expected one of {sorted(HANDOFF_ALLOWED_STAGES)}.",
                severity=HandoffIssueSeverity.ERROR,
            )
        )
        return fallback
    return normalized


def _normalize_handoff_owner(value: Any, *, issues: list[HandoffContractIssue]) -> str:
    fallback = "human:planner"
    if value is None:
        issues.append(
            HandoffContractIssue(
                code=HandoffIssueCode.MISSING_REQUIRED_FIELD,
                field="handoff_owner",
                message=f"Missing handoff_owner; defaulted to '{fallback}'.",
            )
        )
        return fallback
    if not isinstance(value, str) or not value.strip():
        issues.append(
            HandoffContractIssue(
                code=HandoffIssueCode.INVALID_FIELD_TYPE,
                field="handoff_owner",
                message=f"Invalid handoff_owner; defaulted to '{fallback}'.",
            )
        )
        return fallback
    normalized = value.strip()
    if ":" not in normalized:
        issues.append(
            HandoffContractIssue(
                code=HandoffIssueCode.INVALID_FIELD_VALUE,
                field="handoff_owner",
                message="handoff_owner must use '<kind>:<owner>' format.",
                severity=HandoffIssueSeverity.ERROR,
            )
        )
        return fallback
    kind, owner = normalized.split(":", 1)
    if not kind or not owner:
        issues.append(
            HandoffContractIssue(
                code=HandoffIssueCode.INVALID_FIELD_VALUE,
                field="handoff_owner",
                message="handoff_owner must include both kind and owner.",
                severity=HandoffIssueSeverity.ERROR,
            )
        )
        return fallback
    return normalized


def _normalize_non_empty_string(
    *,
    field_name: str,
    value: Any,
    fallback: str,
    issues: list[HandoffContractIssue],
) -> str:
    if value is None:
        issues.append(
            HandoffContractIssue(
                code=HandoffIssueCode.MISSING_REQUIRED_FIELD,
                field=field_name,
                message=f"Missing {field_name}; defaulted to fallback.",
            )
        )
        return fallback
    if not isinstance(value, str) or not value.strip():
        issues.append(
            HandoffContractIssue(
                code=HandoffIssueCode.INVALID_FIELD_TYPE,
                field=field_name,
                message=f"Invalid {field_name}; defaulted to fallback.",
            )
        )
        return fallback
    return value.strip()


def _normalize_timestamp(value: Any, *, issues: list[HandoffContractIssue]) -> str:
    if value is None:
        issues.append(
            HandoffContractIssue(
                code=HandoffIssueCode.MISSING_REQUIRED_FIELD,
                field="timestamp",
                message="Missing timestamp; generated current UTC timestamp.",
            )
        )
        return _utc_now()
    if not isinstance(value, str) or not value.strip():
        issues.append(
            HandoffContractIssue(
                code=HandoffIssueCode.INVALID_FIELD_TYPE,
                field="timestamp",
                message="Invalid timestamp; generated current UTC timestamp.",
            )
        )
        return _utc_now()

    candidate = value.strip()
    try:
        datetime.fromisoformat(candidate.replace("Z", "+00:00"))
    except ValueError:
        issues.append(
            HandoffContractIssue(
                code=HandoffIssueCode.INVALID_FIELD_VALUE,
                field="timestamp",
                message="timestamp must be valid ISO-8601.",
                severity=HandoffIssueSeverity.ERROR,
            )
        )
        return _utc_now()
    return candidate


def _normalize_validation_status(value: Any, *, issues: list[HandoffContractIssue]) -> HandoffValidationStatus:
    if value is None:
        issues.append(
            HandoffContractIssue(
                code=HandoffIssueCode.MISSING_REQUIRED_FIELD,
                field="validation_status",
                message="Missing validation_status; derived from contract issues.",
            )
        )
        return _build_validation_status(issues=issues)
    if not isinstance(value, Mapping):
        issues.append(
            HandoffContractIssue(
                code=HandoffIssueCode.INVALID_FIELD_TYPE,
                field="validation_status",
                message="validation_status must be an object.",
            )
        )
        return _build_validation_status(issues=issues)

    status_raw = value.get("status", "pass")
    if not isinstance(status_raw, str) or status_raw.strip().lower() not in {"pass", "fail"}:
        issues.append(
            HandoffContractIssue(
                code=HandoffIssueCode.INVALID_FIELD_VALUE,
                field="validation_status.status",
                message="validation_status.status must be 'pass' or 'fail'.",
                severity=HandoffIssueSeverity.ERROR,
            )
        )
        status = "fail"
    else:
        status = status_raw.strip().lower()

    blocking_reasons = _normalize_string_list(
        field_name="validation_status.blocking_reasons",
        value=value.get("blocking_reasons", []),
        issues=issues,
    )
    warnings = _normalize_string_list(
        field_name="validation_status.warnings",
        value=value.get("warnings", []),
        issues=issues,
    )
    derived = _build_validation_status(issues=issues)

    if status == "pass" and derived.status == "fail":
        issues.append(
            HandoffContractIssue(
                code=HandoffIssueCode.INVALID_FIELD_VALUE,
                field="validation_status.status",
                message="validation_status.status cannot be 'pass' while blocking errors exist.",
                severity=HandoffIssueSeverity.ERROR,
            )
        )
        derived = _build_validation_status(issues=issues)
        status = "fail"

    if status == "fail" and not blocking_reasons:
        blocking_reasons = derived.blocking_reasons
    if not warnings:
        warnings = derived.warnings

    return HandoffValidationStatus(status=status, blocking_reasons=blocking_reasons, warnings=warnings)


def _normalize_string_list(*, field_name: str, value: Any, issues: list[HandoffContractIssue]) -> list[str]:
    if isinstance(value, list):
        normalized: list[str] = []
        invalid = False
        for item in value:
            if isinstance(item, str):
                stripped = item.strip()
                if stripped:
                    normalized.append(stripped)
            else:
                invalid = True
        if invalid:
            issues.append(
                HandoffContractIssue(
                    code=HandoffIssueCode.INVALID_FIELD_TYPE,
                    field=field_name,
                    message=f"{field_name} must contain only non-empty strings.",
                )
            )
        return normalized

    issues.append(
        HandoffContractIssue(
            code=HandoffIssueCode.INVALID_FIELD_TYPE,
            field=field_name,
            message=f"{field_name} must be a list of strings.",
        )
    )
    return []


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _build_validation_status(*, issues: list[HandoffContractIssue]) -> HandoffValidationStatus:
    blocking_reasons = [
        issue.message
        for issue in issues
        if issue.severity == HandoffIssueSeverity.ERROR
    ]
    warnings = [
        issue.message
        for issue in issues
        if issue.severity == HandoffIssueSeverity.WARNING
    ]
    return HandoffValidationStatus(
        status="fail" if blocking_reasons else "pass",
        blocking_reasons=blocking_reasons,
        warnings=warnings,
    )
