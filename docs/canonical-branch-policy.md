# Canonical Branch Policy

Issue: `#108`

This repository uses a canonical branch policy for feature execution units:

- Exactly one canonical execution branch per feature.
- Canonical branch format: `NNN-kebab-case` (example: `021-user-onboarding`).
- The branch name is also the canonical `feature_id`.

## Why This Exists

The policy keeps Program/Epic/Feature decomposition operationally consistent by:

- preventing monolithic execution on non-feature branches;
- preserving deterministic mapping between branch and feature artifacts;
- enabling reliable downstream orchestration and validation.

## Native Implementation Boundary

Canonical branch policy is implemented natively in this repository.

- Runtime behavior is sourced from `src/specify_cli/`, `scripts/`, and
  `templates/commands/`.
- External plugin paths under `~/.copilot/installed-plugins/...` are treated as
  design baselines only, never as runtime dependencies.

See the integration traceability matrix:

- `docs/external-baseline-integration-traceability.md`

## Branch-Feature Metadata Contract

The create-feature scripts register branch metadata in:

- `.spec-kit/branch-policy.json`

Contract version:

- `branch-feature.v1`

Shape:

```json
{
  "contract_version": "branch-feature.v1",
  "generated_by": "scripts/python/branch-policy.py",
  "updated_at": "2026-02-26T10:00:00Z",
  "entries": {
    "021-user-onboarding": {
      "branch": "021-user-onboarding",
      "feature_id": "021-user-onboarding",
      "feature_prefix": "021",
      "scope_mode": "feature",
      "source_decision": "feature_mode",
      "parent_epic_id": "epic-authentication",
      "parent_program_id": "program-core-platform",
      "created_at": "2026-02-26T10:00:00Z",
      "updated_at": "2026-02-26T10:00:00Z"
    }
  }
}
```

## Guardrails

- Branch validation rejects non-canonical branch patterns for feature workflows.
- Registration rejects non-feature scope modes (`epic`/`program`) for execution
  units.
- Branch metadata contract validation rejects inconsistent entry state
  (entry key vs `branch`/`feature_id`/`feature_prefix` mismatch).
- Legacy entries missing `branch`/`feature_id`/`feature_prefix` are normalized to canonical values.
- Optional metadata (`parent_epic_id`, `parent_program_id`) accepts missing/null values and requires
  non-empty strings when provided.
- Prefix collisions are blocked (for example, `021-a` and `021-b` for different features).
- Feature directory resolution prefers:
  1. exact match (`specs/<branch>/`);
  2. unique prefix match (`specs/NNN-*`);
  3. default path fallback.
- Ambiguous prefix matches fail with an explicit error.

## Helper Script

Script:

- `scripts/python/branch-policy.py`

Commands:

```bash
python3 scripts/python/branch-policy.py validate --branch 021-user-onboarding
python3 scripts/python/branch-policy.py resolve-feature-dir --repo-root . --branch 021-user-onboarding
python3 scripts/python/branch-policy.py register-feature --repo-root . --branch 021-user-onboarding --feature-id 021-user-onboarding
python3 scripts/python/branch-policy.py register-feature --repo-root . --branch 021-user-onboarding --feature-id 021-user-onboarding --parent-epic-id epic-authentication --parent-program-id program-core-platform
```

## Backward Compatibility

- Non-git mode still works with `SPECIFY_FEATURE`.
- Existing commands keep the same interfaces.
- Policy enforcement is applied where feature-context scripts require a canonical feature branch.
- Re-registering the same branch preserves existing lineage metadata when parent ids are omitted.
  To refresh lineage explicitly, pass `--parent-epic-id` and/or `--parent-program-id`.

## Recovery

If `.spec-kit/branch-policy.json` is missing or corrupted:

- Fix or remove the corrupted file.
- Re-run feature creation for the active branch (or register manually):

```bash
python3 scripts/python/branch-policy.py register-feature --repo-root . --branch 021-user-onboarding --feature-id 021-user-onboarding
```

- Re-run the command that failed (`/speckit.specify`, `/speckit.plan`, or prerequisite checks).
