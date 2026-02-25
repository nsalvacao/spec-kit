# Program/Epic/Feature Hierarchy Contract (v1)

This document defines the canonical Program/Epic/Feature metadata contract used
for decomposition traceability and cross-channel handoffs.

- Module: `src/specify_cli/hierarchy_contract.py`
- Contract version: `program-epic-feature.v1`

## Purpose

Ensure CLI, templates, scripts, and orchestrators share one normalized schema
for hierarchy semantics:

- `program -> epics[]`
- `epic -> features[]`
- `feature -> specs/<feature>/spec.md|plan.md|tasks.md`

## Top-Level Shape

```json
{
  "contract_version": "program-epic-feature.v1",
  "mode": "program",
  "program": {},
  "epics": [],
  "features": []
}
```

## Canonical Invariants

- `features[]` must always include at least one feature.
- `feature` mode requires exactly one feature.
- `epic` and `program` modes require a parent `program`.
- Epic IDs and Feature IDs must be unique.
- Feature `epic_id` references must resolve to declared epics.
- Canonical artifact paths are required:
  - `specs/<feature-id>/spec.md`
  - `specs/<feature-id>/plan.md`
  - `specs/<feature-id>/tasks.md`
- Artifact paths must be relative and must not contain `..` traversal.

## CLI Normalization

Normalize and validate payloads with:

```bash
specify hierarchy-contract --input-json hierarchy.json --output-json .spec-kit/hierarchy-contract.json
```

Use `--strict` to reject unknown top-level fields.

## API Surface

```python
from specify_cli.hierarchy_contract import (
    build_feature_hierarchy_contract,
    normalize_hierarchy_contract_payload,
    validate_hierarchy_contract_payload,
)
```
