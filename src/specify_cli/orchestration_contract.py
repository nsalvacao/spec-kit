"""Programmatic orchestration contract wrapper for multi-channel execution.

Issue: #113
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Mapping
from uuid import UUID, uuid4

from .scope_gate_contract import (
    SCOPE_GATE_CONTRACT_VERSION,
    ScopeGateChannel,
    ScopeGatePayload,
    normalize_scope_gate_payload,
)


ORCHESTRATION_CONTRACT_VERSION = "orchestration-payload.v1"
ORCHESTRATION_ALLOWED_CONTRACT_VERSIONS = frozenset(
    {ORCHESTRATION_CONTRACT_VERSION, SCOPE_GATE_CONTRACT_VERSION}
)
ORCHESTRATION_REQUIRED_FIELDS = frozenset(
    {"contract_version", "request_id", "timestamp", "channel", "scope_gate"}
)


class OrchestrationIssueSeverity(str, Enum):
    """Severity for normalization/validation issues."""

    WARNING = "warning"
    ERROR = "error"


class OrchestrationIssueCode(str, Enum):
    """Known issue codes for orchestration payload normalization."""

    MISSING_REQUIRED_FIELD = "missing_required_field"
    INVALID_FIELD_TYPE = "invalid_field_type"
    INVALID_FIELD_VALUE = "invalid_field_value"
    UNSUPPORTED_CONTRACT_VERSION = "unsupported_contract_version"
    LEGACY_SCOPE_GATE_PAYLOAD = "legacy_scope_gate_payload"


@dataclass(frozen=True)
class OrchestrationContractIssue:
    """Structured issue emitted while validating/normalizing orchestration payloads."""

    code: OrchestrationIssueCode
    field: str
    message: str
    severity: OrchestrationIssueSeverity = OrchestrationIssueSeverity.WARNING

    def to_dict(self) -> dict[str, str]:
        return {
            "code": self.code.value,
            "field": self.field,
            "message": self.message,
            "severity": self.severity.value,
        }


@dataclass(frozen=True)
class OrchestrationPayload:
    """Channel-agnostic orchestration payload envelope."""

    contract_version: str
    request_id: str
    timestamp: str
    channel: ScopeGateChannel
    scope_gate: ScopeGatePayload
    contract_issues: list[OrchestrationContractIssue] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "contract_version": self.contract_version,
            "request_id": self.request_id,
            "timestamp": self.timestamp,
            "channel": self.channel.value,
            "scope_gate": self.scope_gate.to_dict(),
            "contract_issues": [issue.to_dict() for issue in self.contract_issues],
        }


def build_orchestration_payload(
    scope_gate_payload: ScopeGatePayload | Mapping[str, Any],
    *,
    channel: ScopeGateChannel | str = ScopeGateChannel.API,
    request_id: str | None = None,
    timestamp: str | None = None,
) -> OrchestrationPayload:
    """Build orchestration envelope from a scope-gate payload."""
    issues: list[OrchestrationContractIssue] = []
    normalized_scope_gate = _normalize_scope_gate(scope_gate_payload)
    normalized_channel = _normalize_channel(channel, issues=issues)
    normalized_request_id = _normalize_request_id(request_id, issues=issues)
    normalized_timestamp = _normalize_timestamp(timestamp, issues=issues)

    return OrchestrationPayload(
        contract_version=ORCHESTRATION_CONTRACT_VERSION,
        request_id=normalized_request_id,
        timestamp=normalized_timestamp,
        channel=normalized_channel,
        scope_gate=normalized_scope_gate,
        contract_issues=issues,
    )


def normalize_orchestration_payload(
    raw_payload: Mapping[str, Any],
    *,
    strict: bool = False,
) -> OrchestrationPayload:
    """Normalize raw input to orchestration envelope.

    Backward compatibility:
    - If input does not include `scope_gate` but contains scope-gate fields directly,
      it is treated as a legacy `scope-gate-consumption.v1` payload and wrapped.
    """
    if not isinstance(raw_payload, Mapping):
        raise TypeError("raw_payload must be a mapping")

    issues: list[OrchestrationContractIssue] = []

    raw_scope_gate: Any
    if "scope_gate" in raw_payload:
        raw_scope_gate = raw_payload.get("scope_gate")
    else:
        raw_scope_gate = dict(raw_payload)
        issues.append(
            OrchestrationContractIssue(
                code=OrchestrationIssueCode.LEGACY_SCOPE_GATE_PAYLOAD,
                field="scope_gate",
                message=(
                    "Legacy scope-gate payload detected without orchestration envelope; "
                    "wrapped using orchestration-payload.v1 defaults."
                ),
                severity=OrchestrationIssueSeverity.WARNING,
            )
        )

    normalized_scope_gate = _normalize_scope_gate(raw_scope_gate)

    contract_version = raw_payload.get("contract_version")
    if contract_version is None:
        issues.append(
            OrchestrationContractIssue(
                code=OrchestrationIssueCode.MISSING_REQUIRED_FIELD,
                field="contract_version",
                message=f"Missing contract_version; defaulted to {ORCHESTRATION_CONTRACT_VERSION}.",
            )
        )
        normalized_contract_version = ORCHESTRATION_CONTRACT_VERSION
    elif not isinstance(contract_version, str) or not contract_version.strip():
        issues.append(
            OrchestrationContractIssue(
                code=OrchestrationIssueCode.INVALID_FIELD_TYPE,
                field="contract_version",
                message=f"Invalid contract_version; defaulted to {ORCHESTRATION_CONTRACT_VERSION}.",
            )
        )
        normalized_contract_version = ORCHESTRATION_CONTRACT_VERSION
    else:
        normalized_contract_version = contract_version.strip()

    if normalized_contract_version not in ORCHESTRATION_ALLOWED_CONTRACT_VERSIONS:
        issues.append(
            OrchestrationContractIssue(
                code=OrchestrationIssueCode.UNSUPPORTED_CONTRACT_VERSION,
                field="contract_version",
                message=(
                    f"Unsupported contract_version '{normalized_contract_version}'. "
                    f"Supported: {sorted(ORCHESTRATION_ALLOWED_CONTRACT_VERSIONS)}."
                ),
                severity=OrchestrationIssueSeverity.ERROR,
            )
        )

    normalized_channel = _normalize_channel(raw_payload.get("channel"), issues=issues)
    normalized_request_id = _normalize_request_id(raw_payload.get("request_id"), issues=issues)
    normalized_timestamp = _normalize_timestamp(raw_payload.get("timestamp"), issues=issues)

    payload = OrchestrationPayload(
        contract_version=ORCHESTRATION_CONTRACT_VERSION,
        request_id=normalized_request_id,
        timestamp=normalized_timestamp,
        channel=normalized_channel,
        scope_gate=normalized_scope_gate,
        contract_issues=issues,
    )

    if strict:
        error_messages = [issue.message for issue in issues if issue.severity == OrchestrationIssueSeverity.ERROR]
        if error_messages:
            raise ValueError("; ".join(error_messages))

    return payload


def validate_orchestration_payload(
    raw_payload: Mapping[str, Any],
    *,
    strict: bool = False,
) -> list[dict[str, str]]:
    """Validate payload and return normalized issues list."""
    normalized = normalize_orchestration_payload(raw_payload, strict=strict)
    return [issue.to_dict() for issue in normalized.contract_issues]


def _normalize_scope_gate(scope_gate_payload: ScopeGatePayload | Mapping[str, Any] | Any) -> ScopeGatePayload:
    if isinstance(scope_gate_payload, ScopeGatePayload):
        return scope_gate_payload
    if isinstance(scope_gate_payload, Mapping):
        return normalize_scope_gate_payload(scope_gate_payload, strict=False)
    raise TypeError("scope_gate payload must be ScopeGatePayload or mapping")


def _normalize_channel(
    raw_channel: ScopeGateChannel | str | None,
    *,
    issues: list[OrchestrationContractIssue],
) -> ScopeGateChannel:
    if raw_channel is None:
        issues.append(
            OrchestrationContractIssue(
                code=OrchestrationIssueCode.MISSING_REQUIRED_FIELD,
                field="channel",
                message=f"Missing channel; defaulted to {ScopeGateChannel.API.value}.",
            )
        )
        return ScopeGateChannel.API
    if isinstance(raw_channel, ScopeGateChannel):
        return raw_channel
    if isinstance(raw_channel, str):
        normalized = raw_channel.strip().lower()
        for channel in ScopeGateChannel:
            if channel.value == normalized:
                return channel

    issues.append(
        OrchestrationContractIssue(
            code=OrchestrationIssueCode.INVALID_FIELD_VALUE,
            field="channel",
            message=(
                f"Invalid channel value; expected one of {[channel.value for channel in ScopeGateChannel]}. "
                f"Defaulted to {ScopeGateChannel.API.value}."
            ),
            severity=OrchestrationIssueSeverity.ERROR,
        )
    )
    return ScopeGateChannel.API


def _normalize_request_id(
    raw_request_id: str | None,
    *,
    issues: list[OrchestrationContractIssue],
) -> str:
    if raw_request_id is None:
        issues.append(
            OrchestrationContractIssue(
                code=OrchestrationIssueCode.MISSING_REQUIRED_FIELD,
                field="request_id",
                message="Missing request_id; generated UUID value.",
            )
        )
        return str(uuid4())

    if not isinstance(raw_request_id, str) or not raw_request_id.strip():
        issues.append(
            OrchestrationContractIssue(
                code=OrchestrationIssueCode.INVALID_FIELD_TYPE,
                field="request_id",
                message="Invalid request_id; generated UUID value.",
            )
        )
        return str(uuid4())

    candidate = raw_request_id.strip()
    try:
        UUID(candidate)
    except ValueError:
        issues.append(
            OrchestrationContractIssue(
                code=OrchestrationIssueCode.INVALID_FIELD_VALUE,
                field="request_id",
                message="request_id is not a valid UUID; generated UUID value.",
                severity=OrchestrationIssueSeverity.ERROR,
            )
        )
        return str(uuid4())
    return candidate


def _normalize_timestamp(
    raw_timestamp: str | None,
    *,
    issues: list[OrchestrationContractIssue],
) -> str:
    if raw_timestamp is None:
        issues.append(
            OrchestrationContractIssue(
                code=OrchestrationIssueCode.MISSING_REQUIRED_FIELD,
                field="timestamp",
                message="Missing timestamp; generated current UTC timestamp.",
            )
        )
        return _utc_now()

    if not isinstance(raw_timestamp, str) or not raw_timestamp.strip():
        issues.append(
            OrchestrationContractIssue(
                code=OrchestrationIssueCode.INVALID_FIELD_TYPE,
                field="timestamp",
                message="Invalid timestamp type; generated current UTC timestamp.",
            )
        )
        return _utc_now()

    candidate = raw_timestamp.strip()
    try:
        datetime.fromisoformat(candidate.replace("Z", "+00:00"))
    except ValueError:
        issues.append(
            OrchestrationContractIssue(
                code=OrchestrationIssueCode.INVALID_FIELD_VALUE,
                field="timestamp",
                message="timestamp is not valid ISO-8601; generated current UTC timestamp.",
                severity=OrchestrationIssueSeverity.ERROR,
            )
        )
        return _utc_now()

    return candidate


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
