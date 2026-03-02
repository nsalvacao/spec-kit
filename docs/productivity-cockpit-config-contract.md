# Productivity Cockpit Config Contract

This document defines the native A4 contract for cockpit configuration and update
runtime safety.

## Files and Scope

- Cockpit file: `.cockpit.json` (project root)
- Project runtime config: `.specify/spec-kit.yml` section `productivity_update`

`#203` defines this separation intentionally:

- `.cockpit.json` controls cockpit-local behavior (paths, pulse, AI mode details).
- `.specify/spec-kit.yml` controls update engine tuning (thresholds/caps/filters).

## `.cockpit.json` Schema (Versioned)

- `schema_version` (required/normalized): `1`
- `name`: display name
- `version`: cockpit payload version string
- `service`: `{ host, port }`
- `paths`: `{ tasks, tasks_fallback, memory, output }`
- `pulse_rules`: `{ essential_files, min_folders }`
- `ai`: `{ mode, cli, args, provider, model }`

Unknown keys are rejected with actionable errors.

## Path Safety Contract

All configured paths are validated as project-relative and sandboxed:

- absolute paths are rejected;
- path traversal (`..`) is rejected;
- resolved targets must remain under project root;
- symlink escapes outside project root are rejected.

This applies to update read/write paths and external task file ingestion.

## AI Contract (`ai.mode` / `ai.cli`)

- Allowed `ai.mode`: `cli`, `api`
- `ai.cli` default is intentionally neutral (`""`) to avoid hardcoded provider bias.
- `ai.cli: ""` remains valid for migration compatibility.
- `ai.cli` may be required later by command-specific runtime behavior (A3+), but
  A4 keeps validation compatible with existing generated configs.

## Migration Compatibility

Legacy `.cockpit.json` files without `schema_version` are accepted and normalized
to schema version `1`.

Compatibility guarantee for pre-A4 files:

- Existing `ai.cli: ""` remains valid.
- Missing optional keys are defaulted deterministically.
- Invalid types/unsafe paths fail fast with clear recovery guidance.

## Privacy and Logging Hygiene

- The runtime is local-first by default.
- File path validation errors are explicit but avoid secret leakage.
- No AI credentials are stored in `.cockpit.json` by contract.

## `productivity_update` Runtime Tuning

Configured in `.specify/spec-kit.yml` with standard precedence (defaults -> project
-> local override -> env).

Supported keys:

- `fuzzy_title_match_threshold` (float > 0 and <= 1)
- `default_stale_age_days` (int)
- `max_comprehensive_scan_files` (int)
- `max_comprehensive_scan_file_bytes` (int)
- `common_entity_stopwords` (list[str])
- `common_entity_verbish` (list[str])

Env override examples:

- `SPECIFY_CONFIG__PRODUCTIVITY_UPDATE__DEFAULT_STALE_AGE_DAYS=21`
- `SPECIFY_CONFIG__PRODUCTIVITY_UPDATE__FUZZY_TITLE_MATCH_THRESHOLD=0.9`
