# Configuration

Spec-Kit supports centralized runtime configuration through project files under
`.specify/`.

## Canonical Files

- `.specify/spec-kit.yml`:
  - Project-shared configuration.
  - Intended to be committed.
- `.specify/spec-kit.local.yml`:
  - Local machine/user overrides.
  - Intended to be gitignored.

During `specify init`, `.specify/spec-kit.yml` is initialized from
`.specify/templates/spec-kit-config-template.yml` when missing.

## Precedence

Configuration is merged with the following order (lowest -> highest):

1. Built-in defaults
2. `.specify/spec-kit.yml`
3. `.specify/spec-kit.local.yml`
4. `SPECIFY_CONFIG__...` environment overrides

## Environment Override Format

Use `SPECIFY_CONFIG__` and `__` path separators:

- `SPECIFY_CONFIG__SCOPE_DETECTION__WORK_ITEMS_MULTIPLIER=2`
- `SPECIFY_CONFIG__SCOPE_DETECTION__RISK_WEIGHTS__HIGH=10`

Values are parsed as YAML scalars/collections.

## Current Configurable Section: Scope Detection

The adaptive scope engine currently consumes:

- `scope_detection.feature_max_score`
- `scope_detection.epic_max_score`
- `scope_detection.max_total_score`
- `scope_detection.*_multiplier` and `*_cap` signal settings
- `scope_detection.risk_weights`
- `scope_detection.complexity_keywords`
- `scope_detection.confidence_*` heuristics

See full contract and examples in:

- `docs/adaptive-scope-detection-contract.md`
- `docs/scope-scoring-rubric.md`

## Current Configurable Section: Productivity Update Runtime

The native productivity update engine (`specify productivity update`) consumes:

- `productivity_update.fuzzy_title_match_threshold`
- `productivity_update.default_stale_age_days`
- `productivity_update.max_comprehensive_scan_files`
- `productivity_update.max_comprehensive_scan_file_bytes`
- `productivity_update.common_entity_stopwords`
- `productivity_update.common_entity_verbish`

These values tune matching/triage depth and scan limits without hardcoding policy in code.

See full contract and cockpit safety model in:

- `docs/productivity-cockpit-config-contract.md`

## Current Configurable Section: Strategic Review Runtime

The strategic readiness gate (`/speckit.strategic-review`) consumes:

- `strategic_review.weights.output_quality`
- `strategic_review.weights.readme_docs_quality`
- `strategic_review.weights.developer_experience`
- `strategic_review.weights.security_trust`
- `strategic_review.weights.competitive_positioning`
- `strategic_review.weights.test_coverage`
- `strategic_review.thresholds.green_min_score`
- `strategic_review.thresholds.yellow_min_score`
- `strategic_review.blockers.emit_on_bands`
- `strategic_review.blockers.max_items`
- `strategic_review.validator.min_sections`
- `strategic_review.validator.min_line_count`

These keys control weighted launch-readiness scoring, score-band mapping, and
automatic blocker artifact emission.

## Reuse Guidance for Future Features

When adding new configurable behavior in Spec-Kit:

1. Add a new top-level section in `.specify/spec-kit.yml`.
2. Keep built-in defaults in code for backward compatibility.
3. Load via `src/specify_cli/project_config.py`.
4. Validate schema and types explicitly in the consuming module.
5. Document keys and precedence in this file.
