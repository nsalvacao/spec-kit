# Adaptive Scope Detection Contract (v1)

This document defines the **versioned output contract** for the adaptive scope
detection engine introduced for issue `#101`.

- Module: `src/specify_cli/scope_detection.py`
- Contract version: `scope-detection.v1`
- Purpose: deterministically recommend `feature`, `epic`, or `program` mode
  before decomposition/task generation.
- Config object: `ScopeDetectionConfig` (all weights/caps/keywords are
  centralized and overridable; not scattered as hardcoded magic numbers).
- Canonical rubric specification: `docs/scope-scoring-rubric.md`
  (`scope-scoring-rubric.v1`).
- Project config source: `.specify/spec-kit.yml` plus optional
  `.specify/spec-kit.local.yml` and `SPECIFY_CONFIG__...` env overrides.
- Global configuration rules and precedence: `docs/configuration.md`.

## Score Bands

| Score | Mode | Expected behavior |
| --- | --- | --- |
| `0-34` | `feature` | Proceed as single feature pipeline |
| `35-64` | `epic` | Decompose epic into features before task generation |
| `65+` | `program` | Decompose program into epics and then features |

## Input Model

`ScopeDetectionInput` fields:

- `description: str` (required)
- `estimated_timeline_weeks: int` (>=1)
- `expected_work_items: int` (>=1)
- `dependency_count: int` (>=0)
- `integration_surface_count: int` (>=0)
- `domain_count: int` (>=1)
- `cross_team_count: int` (>=1)
- `risk_level: "low" | "medium" | "high" | "critical"`
- `requires_compliance_review: bool`
- `requires_migration: bool`

Validation errors are raised as `ValueError` for invalid inputs.
Type errors are raised as `TypeError` for invalid runtime types.

## Configuration Model

`ScopeDetectionConfig` controls:

- score boundaries (`feature_max_score`, `epic_max_score`)
- per-signal multipliers/caps (timeline, work items, dependencies, etc.)
- risk weights map (`risk_weights`)
- keyword set (`complexity_keywords`)
- confidence heuristics and clamping

You can pass a custom config at call time:

```python
from specify_cli.scope_detection import ScopeDetectionConfig, ScopeDetectionInput, detect_scope

config = ScopeDetectionConfig(
    work_items_multiplier=2,
    dependency_multiplier=1,
    complexity_keywords=frozenset({"platform", "migration"}),
)

result = detect_scope(
    ScopeDetectionInput(description="Platform migration for billing"),
    config=config,
)
```

Or load from project configuration:

```python
from pathlib import Path
from specify_cli.scope_detection import ScopeDetectionInput, detect_scope_for_project

result = detect_scope_for_project(
    ScopeDetectionInput(description="Platform migration for billing"),
    project_root=Path("."),
)
```

## Scoring Signals (Deterministic)

The engine calculates score contributions from these signals:

- timeline length
- expected work items
- dependency count
- integration surface count
- domain breadth
- cross-team coordination
- declared risk level
- compliance requirement
- migration/cutover requirement
- complexity keywords detected in description (whole-keyword matching, not
  naive substring matching)

Each signal is emitted in the output `signals` array with:

- `name`
- `value`
- `weight`
- `score`
- `rationale`

For the canonical dimension table (weights, formulas, tie-break rules, and
rationale template), see `docs/scope-scoring-rubric.md`.
Downstream consumers can validate rubric payload structure via
`validate_scope_scoring_rubric_payload(...)`.

## Output Contract

The engine returns `ScopeDetectionResult`. `to_dict()` emits:

```json
{
  "contract_version": "scope-detection.v1",
  "total_score": 42,
  "score_band": "35-64",
  "mode_recommendation": "epic",
  "recommendation_reasons": [
    "...",
    "..."
  ],
  "confidence": 0.79,
  "signals": [
    {
      "name": "dependency_count",
      "value": 3,
      "weight": 3,
      "score": 9,
      "rationale": "..."
    }
  ]
}
```

### Required Downstream Keys

The contract guarantees at least:

- `mode_recommendation`
- `recommendation_reasons` (2-3 entries)
- `confidence`
- `signals`

Additional fields (`contract_version`, `total_score`, `score_band`) are included
to support observability and future compatibility checks.
