# Scope Gate Consumption Contract (v1)

This document defines the stable, channel-agnostic contract for consuming scope
detection output in orchestrators, gates, and downstream handlers.

- Module: `src/specify_cli/scope_gate_contract.py`
- Contract version: `scope-gate-consumption.v1`
- Related detector contract: `docs/adaptive-scope-detection-contract.md`

## Purpose

Ensure CLI, TTY/TUI, and programmatic API flows interpret scope decisions with
the same semantics and fallback behavior.

## Required Fields

| Field | Description |
| --- | --- |
| `mode_recommendation` | Recommended scope mode from detector (`feature`, `epic`, `program`) |
| `recommendation_reasons` | Human-readable rationale list (2-3 reasons) |
| `user_choice` | Final selected mode |
| `override_flag` | Whether `user_choice` differs from `mode_recommendation` |
| `next_action` | Immediate action/command after gate resolution |
| `handoff_owner` | Human/agent owner for next stage |
| `artifacts_created` | Canonical artifact paths created by this step |
| `validation_status` | Pass/fail plus blocking reasons/warnings |

## Payload Shape

```json
{
  "contract_version": "scope-gate-consumption.v1",
  "mode_recommendation": "epic",
  "recommendation_reasons": [
    "3 external dependencies increase coordination and operational risk (9 points).",
    "2 involved domains indicate scope breadth (10 points)."
  ],
  "user_choice": "epic",
  "override_flag": false,
  "next_action": "Decompose epic into features before generating tasks.",
  "handoff_owner": "human:planner",
  "artifacts_created": [
    "specs/021-identity/tasks.md"
  ],
  "validation_status": {
    "status": "pass",
    "blocking_reasons": [],
    "warnings": []
  }
}
```

## Error Codes and Fallback Rules

The normalizer (`normalize_scope_gate_payload`) accepts partial/invalid input
and applies deterministic fallback behavior while recording issues.

| Code | Trigger | Fallback |
| --- | --- | --- |
| `missing_required_field` | Required field absent | Deterministic default for that field |
| `invalid_field_type` | Field has wrong type | Deterministic default for that field |
| `invalid_field_value` | Field value outside accepted domain | Deterministic default for that field |
| `invalid_artifact_path` | Invalid artifact path entry | Drop invalid item |
| `unknown_field` | Field not in contract (strict mode) | Validation error (strict mode only) |

Examples:

- Missing `user_choice` -> fallback to `mode_recommendation`
- Missing `override_flag` -> derived from recommendation vs choice
- Missing `next_action` -> derived from selected mode
- Missing `handoff_owner` -> derived from selected mode
- Missing/invalid `validation_status` -> derived from collected issues
- `artifacts_created` must be relative paths (no absolute paths or `..` traversal);
  unsafe entries are dropped and reported as `invalid_artifact_path`.

## API Surface

```python
from specify_cli.scope_gate_contract import (
    build_scope_gate_payload,
    normalize_scope_gate_payload,
    validate_scope_gate_payload,
)
from specify_cli.scope_detection import detect_scope, ScopeDetectionInput

detection = detect_scope(ScopeDetectionInput(description="Cross-team platform migration"))
payload = build_scope_gate_payload(detection)         # Internal producer path
normalized = normalize_scope_gate_payload(payload.to_dict())  # External consumer path
issues = validate_scope_gate_payload(payload.to_dict(), strict=True)
```

## Channel Integration Examples

CLI:
- Show recommendation + reasons
- Ask user to follow or override
- Persist `user_choice`, `override_flag`, `next_action`, `handoff_owner`

TTY/TUI:
- Present compact decision prompt
- Include explicit next action and handoff owner in terminal summary

Programmatic API:
- Consume machine-readable payload directly
- Validate with `validate_scope_gate_payload(..., strict=True)` before acting

## Versioning and Compatibility

- Current version: `scope-gate-consumption.v1`
- Backward-compatible additive fields are allowed
- Breaking shape/semantic changes require version bump
- Strict validators should reject unknown fields when strict mode is enabled
