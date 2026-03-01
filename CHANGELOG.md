# Changelog

<!-- markdownlint-disable MD024 -->

All notable changes to the Specify CLI and templates are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.0.75] - 2026-03-01

### Added

- *No changes documented yet.*

### Added

- **#200: Native productivity start flow (A1 cockpit bootstrap)**
  - Added `specify productivity start` command to initialize `TASKS.md`, `CLAUDE.md`,
    `memory/`, and `.cockpit.json` idempotently.
  - Added native local cockpit bridge bootstrap with status endpoint and dashboard page.
  - Added compact JSON output mode and scaffold-only operation (`--no-server`/`--no-browser`).

## [0.0.74] - 2026-03-01

### Added

- *No changes documented yet.*

## [0.0.73] - 2026-02-27

### Added

- *No changes documented yet.*

### Added

- **#142: Automated Google Drive release backup (OAuth refresh-token model)**
  - Added workflow `.github/workflows/backup-gdrive.yml` (release-triggered + manual dispatch).
  - Added uploader utility `scripts/python/gdrive-release-backup.py`:
    - OAuth refresh-token exchange to short-lived access token
    - deterministic archive checksum/manifest generation
    - Drive upsert by folder ID
    - manifest-based retention with retry/backoff handling
  - Added operations documentation: `docs/backup-google-drive.md`.
  - Updated release process documentation for backup prerequisites and behavior.

## [0.0.71] - 2026-02-27

### Added

- *No changes documented yet.*

### Changed

- Release automation now keeps metadata aligned by running
  `Release Metadata Sync` on `Create Release` completion (`workflow_run`) and on
  direct `release: published` events.
- Removed the `pyproject.toml` update step that only mutated release-runner
  artifacts to avoid non-persistent version changes and future drift.

## [0.0.70] - 2026-02-27

### Added

- **#35 (P030): Full scoring coverage validation in `validate-airice.sh` / `validate-airice.ps1`**
  - Added second optional argument `BACKLOG_PATH` (default: `.spec-kit/ideas_backlog.md`)
    to both bash and PowerShell validators.
  - When the backlog file exists, the validator now checks that every idea listed in
    `ideas_backlog.md` has a corresponding row in the `idea_selection.md` scoring table.
  - On failure, the error output shows: total ideas in backlog, total scored rows,
    and the list of missing idea IDs.
  - Coverage check is skipped gracefully when the backlog file is absent.
  - Added test coverage in `tests/test_airice_calculator.py`:
    `TestValidateAIRiceCoverageBash` and `TestValidateAIRiceCoveragePS1`.

- **#171: Branch policy lineage metadata + inconsistency/rollback regressions**
  - Added optional lineage fields to branch metadata contract registration:
    - `parent_epic_id`
    - `parent_program_id`
  - Added contract consistency checks to fail fast when metadata diverges from canonical branch identity.
  - Added rollback regression tests for feature creation flows:
    - `tests/test_create_new_feature_rollback.py` (bash + PowerShell parity)
  - Extended branch policy tests for lineage and inconsistency scenarios:
    - `tests/test_branch_policy.py`

- **#176: Command discoverability audit — amend + global coverage**
  - Added `/speckit.amend`, `/speckit.validate`, `/speckit.taskstoissues` to
    the "Next Steps" panel shown after `specify init`.
  - Reordered commands in "Next Steps" to follow canonical workflow sequence.
  - Added "Optional Quality Helpers" section for analyze, checklist,
    taskstoissues.
  - Added regression test: `tests/test_command_discoverability.py`.
  - Added audit report: `docs/command-discoverability-audit.md`.

- **#162: Auto-deploy latest release to Always Free VM**
  - Added `.github/workflows/deploy.yml` triggered on `release: published`
    and `workflow_dispatch`.
  - Added tag validation and deployment summary for traceable operations.
  - Added remote smoke-test step (`~/.local/bin/specify --help`) after install.
  - Hardened SSH deployment path:
    - switched to native runner `ssh` flow (removed third-party SSH action dependency)
    - added VM host-key fingerprint verification (`DEPLOY_VM_HOST_FINGERPRINT`)
    - enabled deploy concurrency cancellation to avoid overlapping deployments
    - added explicit secret validation and key parsing checks before SSH key use
    - switched key/known_hosts artifacts to isolated temp paths with cleanup
    - added support for comma-separated host fingerprints during key rotation windows
    - added required `DEPLOY_VM_KNOWN_HOSTS` host-key pinning variable (no runtime `ssh-keyscan` fallback)
    - added optional `DEPLOY_VM_PORT` workflow variable for non-default SSH ports
    - added strict `known_hosts` entry validation (one or more entries, non-hashed host, `ssh-ed25519`, host-field sanity checks)
    - rejected wildcard/ambiguous host values in deploy host pinning validation
    - improved remote diagnostics for missing `uv`/`specify` binaries during deploy
    - added explicit smoke-test status and exit-code reporting in deployment job summary
    - switched SSH artifact cleanup to best-effort secure deletion (`shred`) with safe fallback

- **#165: Unified version orchestration (manifest + bump engine + coherence gate)**
  - Added manifest source of truth: `.github/version-map.yml`.
  - Added orchestration engine: `scripts/python/version-orchestrator.py` with `check`, `bump`, and `sync`.
  - Added cross-platform bump wrappers:
    - `scripts/bash/version-bump.sh`
    - `scripts/powershell/version-bump.ps1`
  - Added CI coherence gate:
    - `.github/workflows/version-coherence.yml`
  - Added regression test suite:
    - `tests/test_version_orchestrator.py`
- **#113: Programmatic orchestration contract (channel-agnostic envelope)**
  - Added `src/specify_cli/orchestration_contract.py` with versioned envelope `orchestration-payload.v1`.
  - Added helper script and wrappers:
    - `scripts/python/orchestration-contract.py`
    - `scripts/bash/orchestration-contract.sh`
    - `scripts/powershell/orchestration-contract.ps1`
  - Added docs and script regression tests:
    - `docs/programmatic-orchestration-contract.md`
    - `tests/test_orchestration_contract.py`
    - `tests/test_orchestration_contract_script.py`
- **#115: Template/script instruction contract for LLM agents**
  - Added instruction contract validator module: `src/specify_cli/template_instruction_contract.py`.
  - Added validator script and wrappers:
    - `scripts/python/template-instruction-contract.py`
    - `scripts/bash/template-instruction-contract.sh`
    - `scripts/powershell/template-instruction-contract.ps1`
  - Updated core command templates (`specify`, `clarify`, `plan`, `tasks`) with required instruction-contract markers.
  - Added docs and tests:
    - `docs/template-instruction-contract.md`
    - `tests/test_template_instruction_contract.py`
- **#116: Handoff metadata schema + lint/validation gate**
  - Added handoff schema/normalization module: `src/specify_cli/handoff_contract.py` (`handoff-metadata.v1`).
  - Added template/payload lint gate module: `src/specify_cli/handoff_metadata_lint.py`.
  - Added lint script and wrappers:
    - `scripts/python/handoff-metadata-lint.py`
    - `scripts/bash/handoff-metadata-lint.sh`
    - `scripts/powershell/handoff-metadata-lint.ps1`
  - Added schema documentation and regression tests:
    - `docs/handoff-metadata-schema-contract.md`
    - `tests/test_handoff_contract_gate.py`

### Changed

- **Release metadata sync automation**
  - Updated `.github/workflows/release-metadata-sync.yml` to use `version-orchestrator.py sync`.
  - Metadata sync now propagates to `uv.lock` in addition to `pyproject.toml` and `CHANGELOG.md`.
- **Baseline promotion sync automation**
  - Added `.github/workflows/baseline-auto-sync.yml` to detect open `baseline/* -> main`
    PRs and auto-trigger GitHub's "Update branch" when `main` moves ahead.
  - Added manual entry point (`workflow_dispatch`) with optional PR number targeting.
  - Added release-process and Copilot workflow documentation for the new sync behavior.

## [0.0.53] - 2026-02-26

### Added

- **#107: Program/Epic/Feature hierarchy model and metadata contract**
  - Added `src/specify_cli/hierarchy_contract.py` with:
    - canonical entities (`ProgramMetadata`, `EpicMetadata`, `FeatureMetadata`)
    - versioned payload contract (`program-epic-feature.v1`)
    - normalizer/validator helpers for cross-channel payload consistency
  - Added `specify hierarchy-contract` CLI command for payload normalization and validation.
  - Added contract documentation: `docs/hierarchy-metadata-contract.md`.
  - Added test suites:
    - `tests/test_hierarchy_contract.py`
    - `tests/test_hierarchy_contract_cli.py`
  - Updated templates and command prompts to reference hierarchy metadata lineage across `spec`, `plan`, and `tasks` flows.
- **#108: canonical branch policy for multi-feature initiatives**
  - Added branch policy helper: `scripts/python/branch-policy.py`.
  - Added canonical branch metadata contract file:
    - `.spec-kit/branch-policy.json` (`branch-feature.v1`)
  - Added branch policy documentation:
    - `docs/canonical-branch-policy.md`
  - Added regression tests for validation, registration, prefix-collision, and path-resolution:
    - `tests/test_branch_policy.py`
- **#106: decomposition gate flow with explicit override/risk controls**
  - Added gate flow module with deterministic state machine:
    `detect -> recommend -> choose -> confirm -> handoff`.
  - Added `specify scope-gate` command with decision options:
    `follow`, `inspect_rationale`, `override`.
  - Enforced mandatory override rationale and risk acknowledgment for risky overrides (`epic`/`program` recommendations).
  - Added test suites for module and CLI flow coverage:
    - `tests/test_decomposition_gate.py`
    - `tests/test_scope_gate_cli.py`
  - Updated tasks command guidance to require gate payload before task generation.
- **#104: scope detection boundary and regression test hardening**
  - Added low/medium/high complexity fixtures for reusable test inputs.
  - Added neighbor-boundary regression coverage around 34/35 and 64/65 bands.
  - Added threshold/weight regression matrix tests to detect classification drift.
- **#103: scope detection runtime integration and structured gate handoff**
  - Added strict input parser/normalizer for detector payloads: `scope_detection_input_from_mapping(...)`.
  - Added `specify scope-detect` command to execute project-config-aware detection and emit parseable JSON.
  - Command now emits combined payloads for downstream orchestration:
    - `scope_detection` (detector contract output)
    - `scope_gate` (stable gate-consumption contract output)

### Changed

- **CLI hardening (`hierarchy-contract`)**:
  - Added `--project-root` option and enforced resolved-path containment for `--input-json` and `--output-json`.
  - Added regression tests for outside-root and symlink-escape scenarios in `tests/test_hierarchy_contract_cli.py`.
- **Version metadata**:
  - Bumped CLI package version to `0.0.53` in `pyproject.toml` and aligned local package entry in `uv.lock`.
- **CI resilience for Dependabot contexts (`#161`)**:
  - Added preflight policy in `ai-review.yml` to gracefully skip model inference when `MODELS_PAT` is unavailable in bot/untrusted contexts.
  - Kept strict failure behavior for missing `MODELS_PAT` in trusted internal contexts.
  - Added explicit skip timeline/summary notes so skipped inference is traceable in workflow logs.
  - Added protection to skip inference for `dependabot[bot]` PRs that modify `.github/workflows/**`.
- **Dependabot policy alignment (`#161`)**:
  - Expanded `.github/dependabot.yml` with explicit cadence window (Europe/Lisbon), PR limits, labels, and target branch.
  - Added conservative minor/patch grouping for `github-actions` and `pip` plus direct-dependency focus for Python updates.

## [0.0.52] - 2026-02-19

### Added

- **#105: Stable gate consumption contract for CLI/TTY/API (`scope-gate-consumption.v1`)**
  - Added channel-agnostic contract module: `src/specify_cli/scope_gate_contract.py`
  - Added typed payload builders/normalizers:
    - `build_scope_gate_payload(...)`
    - `normalize_scope_gate_payload(...)`
    - `validate_scope_gate_payload(...)`
  - Added explicit error codes, strict validation mode, and deterministic fallback rules
  - Added contract documentation: `docs/scope-gate-consumption-contract.md`
  - Added contract test suite: `tests/test_scope_gate_contract.py`
- **Upstream #1506 hardening (credit: Daniel Hashmi, @DanielHashmi)**: smart `.specify` detection now preserves existing project state by default when re-running `specify init` in current directory.
  - Added safe `.specify` detection helper (`detect_existing_specify_state`) with symlink-aware behavior.
  - Added explicit guard: `--force` refuses to overwrite symlinked `.specify` directories.
  - Added regression tests: `tests/test_specify_detection.py`.

### Changed

- **CI (`ai-review.yml`)**: kept large-diff review fixes in this PR scope and improved output/debug traceability.
  - Version metadata aligned to `0.0.52` to keep monotonic progression after published release `v0.0.51`.
  - Review model selection is now configurable via repository variables (`REVIEW_LONG_CONTEXT_MODEL`, `REVIEW_MODEL`, `REVIEW_FALLBACK_MODEL`) instead of fixed IDs.
  - Added A/B model selection via repository variables (`REVIEW_AB_MODE=parity`, `REVIEW_AB_MODELS=modelA,modelB,...`) with deterministic PR-based bucketing.
  - Added startup validation for `MODELS_PAT` (`GH_MODELS_TOKEN`) to fail fast on missing secret.
  - Added tenant catalog pre-check (`/catalog/models`) to skip unavailable configured models before attempting inference.
  - Long-context model fallback now treats `400/401/403/404` as non-retryable per model to avoid wasted retry loops.
  - Full-diff reviews now write `review.md` deterministically before posting the PR comment.
  - Added append-only UTC timeline logging (`review_timeline.md`) for model attempts, HTTP status, retry backoff, rate-limit headers, and chunk progress.
  - Exported the timeline to the workflow run summary for easier incident debugging.
- **Init hardening (`.specify` symlink mode)**:
  - Skip bootstrap mutations inside `.specify` (`chmod`, constitution bootstrap, project config bootstrap) when `.specify` is a symlink.
  - Added regression tests to ensure symlinked `.specify` never receives implicit writes during those bootstrap steps.

## [0.0.48] - 2026-02-19

### Added

- **Upstream #1386**: `--local-templates` option for local template consumption.
- **Upstream #1480**: `--keep-memory` flag for preserving constitution during agent switches.
- **#101**: adaptive scope detection engine with deterministic scoring and structured output.
- **#102**: canonical scope scoring rubric (`scope-scoring-rubric.v1`) and schema validation helpers.

### Changed

- Release-level updates and process/docs fixes published in this window.
- Full commit list and artifacts: `https://github.com/nsalvacao/spec-kit/releases/tag/v0.0.48`

## [0.0.47] - 2026-02-19

### Changed

- Release notes: `https://github.com/nsalvacao/spec-kit/releases/tag/v0.0.47`

## [0.0.46] - 2026-02-19

### Changed

- Release notes: `https://github.com/nsalvacao/spec-kit/releases/tag/v0.0.46`

## [0.0.45] - 2026-02-19

### Changed

- Release notes: `https://github.com/nsalvacao/spec-kit/releases/tag/v0.0.45`

## [0.0.44] - 2026-02-19

### Changed

- Release notes: `https://github.com/nsalvacao/spec-kit/releases/tag/v0.0.44`

## [0.0.43] - 2026-02-19

### Changed

- Release notes: `https://github.com/nsalvacao/spec-kit/releases/tag/v0.0.43`

## [0.0.42] - 2026-02-19

### Changed

- Release notes: `https://github.com/nsalvacao/spec-kit/releases/tag/v0.0.42`

## [0.0.41] - 2026-02-19

### Changed

- Release notes: `https://github.com/nsalvacao/spec-kit/releases/tag/v0.0.41`

## [0.0.40] - 2026-02-19

### Changed

- Release notes: `https://github.com/nsalvacao/spec-kit/releases/tag/v0.0.40`

## [0.0.39] - 2026-02-19

### Changed

- Release notes: `https://github.com/nsalvacao/spec-kit/releases/tag/v0.0.39`

## [0.0.38] - 2026-02-18

### Changed

- Release notes: `https://github.com/nsalvacao/spec-kit/releases/tag/v0.0.38`

## [0.0.37] - 2026-02-18

### Changed

- Release notes: `https://github.com/nsalvacao/spec-kit/releases/tag/v0.0.37`

## [0.0.36] - 2026-02-18

### Changed

- Release notes: `https://github.com/nsalvacao/spec-kit/releases/tag/v0.0.36`

## [0.0.35] - 2026-02-18

### Changed

- Release notes: `https://github.com/nsalvacao/spec-kit/releases/tag/v0.0.35`

## [0.0.34] - 2026-02-18

### Changed

- Release notes: `https://github.com/nsalvacao/spec-kit/releases/tag/v0.0.34`

## [0.0.33] - 2026-02-18

### Changed

- Release notes: `https://github.com/nsalvacao/spec-kit/releases/tag/v0.0.33`

## [0.0.32] - 2026-02-18

### Changed

- Release notes: `https://github.com/nsalvacao/spec-kit/releases/tag/v0.0.32`

## [0.0.31] - 2026-02-18

### Changed

- Release notes: `https://github.com/nsalvacao/spec-kit/releases/tag/v0.0.31`

## [0.0.30] - 2026-02-18

### Changed

- Release notes: `https://github.com/nsalvacao/spec-kit/releases/tag/v0.0.30`

## [0.0.29] - 2026-02-18

### Changed

- Release notes: `https://github.com/nsalvacao/spec-kit/releases/tag/v0.0.29`

## [0.0.28] - 2026-02-18

### Changed

- Release notes: `https://github.com/nsalvacao/spec-kit/releases/tag/v0.0.28`

## [0.0.27] - 2026-02-18

### Changed

- Release notes: `https://github.com/nsalvacao/spec-kit/releases/tag/v0.0.27`

## [0.0.26] - 2026-02-18

### Changed

- Release notes: `https://github.com/nsalvacao/spec-kit/releases/tag/v0.0.26`

## [0.0.25] - 2026-02-18

### Fixed

- **P002 (#9): state-init yq hard-dependency** - Removed spurious `yq` hard-dependency from `state-init.sh` and `state-init.ps1`
  - Both scripts only write static YAML via heredoc/Set-Content; yq was never invoked
  - Fixes init failure on systems without yq installed
- **P003 (#19): ripgrep not enforced at init** - `specify init` now checks for `rg` (ripgrep) at startup
  - Shows a prominent yellow warning panel when ripgrep is not installed
  - Warning includes install instructions for Linux/macOS/Windows/Cargo
  - Initialisation continues (rg is not required for `init`; validators need it)
  - `precheck` tracker step now reflects `rg` availability accurately

### Security

- **Workflow permissions** - Added explicit `permissions` to all reusable workflow callers
  - `ai-review.yml` jobs: `contents: read`, `pull-requests: write`
  - `ai-triage.yml` job: `contents: read`, `issues: write`
  - Resolves CodeQL alerts #7, #8, #9 (Medium — missing permissions)

## [0.0.24] - 2026-02-18

### Changed

- **Versioning**: Simplified version scheme to standard `MAJOR.MINOR.PATCH` (SemVer), dropping the `-fork.N` suffix.
  - `pyproject.toml` version is now PEP 440 compliant.
  - `get-next-version.sh` now correctly parses patch versions that include pre-release suffixes.
- **CI**: Added `test.yml` GitHub Actions workflow — runs `pytest` on every push to `main` and on PRs.
- **CI**: Fixed `get-next-version.sh` to correctly extract the numeric patch component from fork-style version tags.

## [0.0.23-fork.1] - 2026-01-14

### Added

- Fork version following the versioning scheme: upstream base version with fork suffix.

## [0.0.23] - 2026-01-13

### Added

- Support for overriding the template source via `SPECIFY_TEMPLATE_REPO` or `--template-repo` during `specify init`.
- Core dependency checks (python, uv, yq, rg) surfaced in `specify check` and prerequisite scripts.
- Phase 0 command documentation updates in README/installation.

## [0.0.22] - 2025-11-07

- Support for VS Code/Copilot agents, and moving away from prompts to proper agents with hand-offs.
- Move to use `AGENTS.md` for Copilot workloads, since it's already supported out-of-the-box.
- Adds support for the version command. ([#486](https://github.com/github/spec-kit/issues/486))
- Fixes potential bug with the `create-new-feature.ps1` script that ignores existing feature branches when determining next feature number ([#975](https://github.com/github/spec-kit/issues/975))
- Add graceful fallback and logging for GitHub API rate-limiting during template fetch ([#970](https://github.com/github/spec-kit/issues/970))

## [0.0.21] - 2025-10-21

- Fixes [#975](https://github.com/github/spec-kit/issues/975) (thank you [@fgalarraga](https://github.com/fgalarraga)).
- Adds support for Amp CLI.
- Adds support for VS Code hand-offs and moves prompts to be full-fledged chat modes.
- Adds support for `version` command (addresses [#811](https://github.com/github/spec-kit/issues/811) and [#486](https://github.com/github/spec-kit/issues/486), thank you [@mcasalaina](https://github.com/mcasalaina) and [@dentity007](https://github.com/dentity007)).
- Adds support for rendering the rate limit errors from the CLI when encountered ([#970](https://github.com/github/spec-kit/issues/970), thank you [@psmman](https://github.com/psmman)).

## [0.0.20] - 2025-10-14

### Added

- **Intelligent Branch Naming**: `create-new-feature` scripts now support `--short-name` parameter for custom branch names
  - When `--short-name` provided: Uses the custom name directly (cleaned and formatted)
  - When omitted: Automatically generates meaningful names using stop word filtering and length-based filtering
  - Filters out common stop words (I, want, to, the, for, etc.)
  - Removes words shorter than 3 characters (unless they're uppercase acronyms)
  - Takes 3-4 most meaningful words from the description
  - **Enforces GitHub's 244-byte branch name limit** with automatic truncation and warnings
  - Examples:
    - "I want to create user authentication" → `001-create-user-authentication`
    - "Implement OAuth2 integration for API" → `001-implement-oauth2-integration-api`
    - "Fix payment processing bug" → `001-fix-payment-processing`
    - Very long descriptions are automatically truncated at word boundaries to stay within limits
  - Designed for AI agents to provide semantic short names while maintaining standalone usability

### Changed

- Enhanced help documentation for `create-new-feature.sh` and `create-new-feature.ps1` scripts with examples
- Branch names now validated against GitHub's 244-byte limit with automatic truncation if needed

## [0.0.19] - 2025-10-10

### Added

- Support for CodeBuddy (thank you to [@lispking](https://github.com/lispking) for the contribution).
- You can now see Git-sourced errors in the Specify CLI.

### Changed

- Fixed the path to the constitution in `plan.md` (thank you to [@lyzno1](https://github.com/lyzno1) for spotting).
- Fixed backslash escapes in generated TOML files for Gemini (thank you to [@hsin19](https://github.com/hsin19) for the contribution).
- Implementation command now ensures that the correct ignore files are added (thank you to [@sigent-amazon](https://github.com/sigent-amazon) for the contribution).

## [0.0.18] - 2025-10-06

### Added

- Support for using `.` as a shorthand for current directory in `specify init .` command, equivalent to `--here` flag but more intuitive for users.
- Use the `/speckit.` command prefix to easily discover Spec Kit-related commands.
- Refactor the prompts and templates to simplify their capabilities and how they are tracked. No more polluting things with tests when they are not needed.
- Ensure that tasks are created per user story (simplifies testing and validation).
- Add support for Visual Studio Code prompt shortcuts and automatic script execution.

### Changed

- All command files now prefixed with `speckit.` (e.g., `speckit.specify.md`, `speckit.plan.md`) for better discoverability and differentiation in IDE/CLI command palettes and file explorers

## [0.0.17] - 2025-09-22

### Added

- New `/clarify` command template to surface up to 5 targeted clarification questions for an existing spec and persist answers into a Clarifications section in the spec.
- New `/analyze` command template providing a non-destructive cross-artifact discrepancy and alignment report (spec, clarifications, plan, tasks, constitution) inserted after `/tasks` and before `/implement`.
  - Note: Constitution rules are explicitly treated as non-negotiable; any conflict is a CRITICAL finding requiring artifact remediation, not weakening of principles.

## [0.0.16] - 2025-09-22

### Added

- `--force` flag for `init` command to bypass confirmation when using `--here` in a non-empty directory and proceed with merging/overwriting files.

## [0.0.15] - 2025-09-21

### Added

- Support for Roo Code.

## [0.0.14] - 2025-09-21

### Changed

- Error messages are now shown consistently.

## [0.0.13] - 2025-09-21

### Added

- Support for Kilo Code. Thank you [@shahrukhkhan489](https://github.com/shahrukhkhan489) with [#394](https://github.com/github/spec-kit/pull/394).
- Support for Auggie CLI. Thank you [@hungthai1401](https://github.com/hungthai1401) with [#137](https://github.com/github/spec-kit/pull/137).
- Agent folder security notice displayed after project provisioning completion, warning users that some agents may store credentials or auth tokens in their agent folders and recommending adding relevant folders to `.gitignore` to prevent accidental credential leakage.

### Changed

- Warning displayed to ensure that folks are aware that they might need to add their agent folder to `.gitignore`.
- Cleaned up the `check` command output.

## [0.0.12] - 2025-09-21

### Changed

- Added additional context for OpenAI Codex users - they need to set an additional environment variable, as described in [#417](https://github.com/github/spec-kit/issues/417).

## [0.0.11] - 2025-09-20

### Added

- Codex CLI support (thank you [@honjo-hiroaki-gtt](https://github.com/honjo-hiroaki-gtt) for the contribution in [#14](https://github.com/github/spec-kit/pull/14))
- Codex-aware context update tooling (Bash and PowerShell) so feature plans refresh `AGENTS.md` alongside existing assistants without manual edits.

## [0.0.10] - 2025-09-20

### Fixed

- Addressed [#378](https://github.com/github/spec-kit/issues/378) where a GitHub token may be attached to the request when it was empty.

## [0.0.9] - 2025-09-19

### Changed

- Improved agent selector UI with cyan highlighting for agent keys and gray parentheses for full names

## [0.0.8] - 2025-09-19

### Added

- Windsurf IDE support as additional AI assistant option (thank you [@raedkit](https://github.com/raedkit) for the work in [#151](https://github.com/github/spec-kit/pull/151))
- GitHub token support for API requests to handle corporate environments and rate limiting (contributed by [@zryfish](https://github.com/@zryfish) in [#243](https://github.com/github/spec-kit/pull/243))

### Changed

- Updated README with Windsurf examples and GitHub token usage
- Enhanced release workflow to include Windsurf templates

## [0.0.7] - 2025-09-18

### Changed

- Updated command instructions in the CLI.
- Cleaned up the code to not render agent-specific information when it's generic.

## [0.0.6] - 2025-09-17

### Added

- opencode support as additional AI assistant option

## [0.0.5] - 2025-09-17

### Added

- Qwen Code support as additional AI assistant option

## [0.0.4] - 2025-09-14

### Added

- SOCKS proxy support for corporate environments via `httpx[socks]` dependency

### Fixed

N/A

### Changed

N/A
