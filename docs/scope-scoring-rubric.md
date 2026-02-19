# Scope Scoring Rubric (v1)

This document defines the canonical scoring rubric for adaptive scope
detection.

- Rubric version: `scope-scoring-rubric.v1`
- Engine contract version: `scope-detection.v1`
- Reference implementation: `src/specify_cli/scope_detection.py`
- Programmatic export: `scope_scoring_rubric()`

## Why This Exists

Issue `#102` requires a stable, versionable rubric so multiple agents and
channels can produce equivalent recommendations for `feature`, `epic`, and
`program`.

## Dimensions, Weights, and Scoring Rules

Default values below come from `ScopeDetectionConfig`.

| Dimension | Input Field | Raw Formula | Weight/Rule | Cap |
| --- | --- | --- | --- | --- |
| `timeline_weeks` | `estimated_timeline_weeks` | `max(0, weeks - 1)` | `timeline_multiplier = 1` | `timeline_cap = 10` |
| `expected_work_items` | `expected_work_items` | `max(0, work_items - 1)` | `work_items_multiplier = 5` | `work_items_cap = 20` |
| `dependency_count` | `dependency_count` | `dependency_count` | `dependency_multiplier = 3` | `dependency_cap = 15` |
| `integration_surface_count` | `integration_surface_count` | `integration_surface_count` | `integration_multiplier = 3` | `integration_cap = 12` |
| `domain_count` | `domain_count` | `max(0, domain_count - 1)` | `domain_multiplier = 10` | `domain_cap = 20` |
| `cross_team_count` | `cross_team_count` | `max(0, cross_team_count - 1)` | `cross_team_multiplier = 6` | `cross_team_cap = 12` |
| `risk_level` | `risk_level` | mapped value | `risk_weights = {low:0, medium:6, high:12, critical:18}` | N/A |
| `requires_compliance_review` | `requires_compliance_review` | boolean gate | `compliance_score = 7` when true, else `0` | N/A |
| `requires_migration` | `requires_migration` | boolean gate | `migration_score = 9` when true, else `0` | N/A |
| `complexity_keywords` | `description` | matched keyword count | `1 point / keyword` | `keyword_cap = 12` |

## Aggregation Formula

Score aggregation is deterministic:

```text
total_score = min(max_total_score, sum(signal_scores))
```

With default `max_total_score = 100`.

## Threshold Bands

| Score Range | Recommendation |
| --- | --- |
| `0-34` | `feature` |
| `35-64` | `epic` |
| `65+` | `program` |

Thresholds are configurable via `ScopeDetectionConfig` and
`.specify/spec-kit.yml`.

## Tie-Break Rule for Boundary Cases

Classification is deterministic with inclusive upper bounds:

1. `score <= feature_max_score` -> `feature`
2. `feature_max_score < score <= epic_max_score` -> `epic`
3. `score > epic_max_score` -> `program`

No probabilistic tie-breaking is used for mode selection.

For near-boundary scores, confidence is reduced (not the mode), using:

- boundary distance threshold: `confidence_boundary_distance_threshold` (default `1`)
- boundary penalty: `confidence_boundary_penalty` (default `0.08`)

## Rationale Template Rule

Recommendation reasons are generated with a stable template:

1. Select positive-scoring signals (`score > 0`).
2. Sort by `score desc`, then `signal name asc`.
3. Use top 3 rationales.
4. If fewer than 2 reasons exist, append mode-specific fallback rationale.
5. Return exactly 2-3 reasons.

This guarantees reproducible rationale generation across agents/channels.

## Machine-Readable Rubric API

```python
from specify_cli.scope_detection import scope_scoring_rubric

rubric = scope_scoring_rubric()
print(rubric["score_bands"])
```

Use this API to avoid duplicating hardcoded rubric values in downstream tooling.
