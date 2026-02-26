# Programmatic Orchestration Contract

Issue: `#113`

This contract defines a channel-agnostic envelope for agent orchestration payloads.
It wraps stable scope-gate payloads with execution metadata required by downstream
automation and validators.

- Python helper script: `scripts/python/orchestration-contract.py`
- Cross-platform wrappers:
  - `scripts/bash/orchestration-contract.sh`
  - `scripts/powershell/orchestration-contract.ps1`

## Contract

- Contract version: `orchestration-payload.v1`
- Backward compatibility:
  - Legacy `scope-gate-consumption.v1` payloads are accepted and wrapped.

### Required top-level fields

- `contract_version`
- `request_id` (UUID)
- `timestamp` (ISO-8601 UTC)
- `channel` (`api` | `cli` | `tty`)
- `scope_gate` (stable `scope-gate-consumption.v1` payload)

Inside `scope_gate`, the required machine-readable fields remain:

- `mode_recommendation`
- `recommendation_reasons`
- `user_choice`
- `override_flag`
- `next_action`
- `handoff_owner`
- `artifacts_created`
- `validation_status`

### Normalization rules

- Missing/invalid envelope fields are normalized to safe defaults in non-strict mode.
- Strict mode fails on unsupported contract versions and invalid critical fields.
- Legacy payload input is preserved through wrapping with an explicit issue marker.

## Python API

- Module: `src/specify_cli/orchestration_contract.py`
- Builders/validators:
  - `build_orchestration_payload(...)`
  - `normalize_orchestration_payload(...)`
  - `validate_orchestration_payload(...)`

## Compatibility policy

- Additive changes are preferred within `v1`.
- Breaking envelope changes must bump contract version and keep legacy wrapper support.

## Local usage

```bash
python3 scripts/python/orchestration-contract.py build --scope-gate .spec-kit/scope-gate.json
python3 scripts/python/orchestration-contract.py normalize --input .spec-kit/orchestration.json
python3 scripts/python/orchestration-contract.py validate --input .spec-kit/orchestration.json
```
