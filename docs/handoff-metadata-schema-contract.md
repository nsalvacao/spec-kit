# Handoff Metadata Schema Contract (v1)

Issue: `#116`

This document defines the machine-readable handoff metadata contract used for
stage transitions in the Spec-Kit pipeline.

- Module: `src/specify_cli/handoff_contract.py`
- Lint/validator module: `src/specify_cli/handoff_metadata_lint.py`
- CLI validator script: `scripts/python/handoff-metadata-lint.py`
- Cross-platform wrappers:
  - `scripts/bash/handoff-metadata-lint.sh`
  - `scripts/powershell/handoff-metadata-lint.ps1`

## Contract summary

- Contract version: `handoff-metadata.v1`
- Supported stages:
  - `ideate`, `select`, `structure`, `validate`, `sdd`
  - `specify`, `clarify`, `plan`, `tasks`, `implement`
- Transition validation is fail-fast for invalid stage moves.

## Required fields

- `contract_version`
- `from_stage`
- `to_stage`
- `handoff_owner`
- `next_action`
- `timestamp`
- `validation_status`

## Validation status semantics

`validation_status` must include:

- `status`: `pass` or `fail`
- `blocking_reasons`: list of blocking issues
- `warnings`: list of non-blocking issues

When missing/invalid, it is derived from contract issues so downstream tools can
always trust a deterministic structure.

## Error codes

- `missing_required_field`
- `invalid_field_type`
- `invalid_field_value`
- `unsupported_contract_version`
- `invalid_stage_transition`

## Local usage

Validate template handoff frontmatter blocks:

```bash
python3 scripts/python/handoff-metadata-lint.py templates --repo-root .
```

Validate a concrete payload file:

```bash
python3 scripts/python/handoff-metadata-lint.py payload --input .spec-kit/scope-gate.json
```
