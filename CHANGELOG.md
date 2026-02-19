# Changelog

<!-- markdownlint-disable MD024 -->

All notable changes to the Specify CLI and templates are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- **Upstream #1386: `--local-templates` option for `specify init`** - Load templates from a local directory instead of GitHub
  - New `--local-templates <path>` option bypasses GitHub download for offline/contributor development testing
  - Searches for `spec-kit-template-<agent>-<script>-*.zip` in the provided directory
  - Shows available templates when no match is found for easier debugging
  - `[DEV MODE]` label in output makes local mode clearly visible
  - Local template ZIP files are preserved after extraction (no cleanup)
- **Upstream #1480: `--keep-memory` option for `specify init`** - Preserve existing `.specify/memory/constitution.md` when switching AI agents
  - New `--keep-memory` flag prevents overwriting existing constitution during template merge
  - Example: `specify init . --ai gemini --keep-memory`
- **#101: Adaptive Scope Detection Engine (`feature` / `epic` / `program`)**
  - Added deterministic scope scoring module: `src/specify_cli/scope_detection.py`
  - Implemented score bands `0-34`, `35-64`, `65+` with stable mode recommendation
  - Added centralized project config loader: `src/specify_cli/project_config.py`
  - Introduced canonical config files:
    - `.specify/spec-kit.yml` (shared)
    - `.specify/spec-kit.local.yml` (local override, gitignored)
  - `specify init` now bootstraps `.specify/spec-kit.yml` from template when missing
  - Centralized scoring weights, caps, boundaries, and keyword set in configurable `ScopeDetectionConfig`
  - Added versioned output contract payload with:
    - `mode_recommendation`
    - `recommendation_reasons`
    - `confidence`
    - `signals`
  - Improved keyword matching to avoid substring false positives
  - Added contract documentation: `docs/adaptive-scope-detection-contract.md`
  - Added unit tests for simple/intermediate/large scenarios and boundary regression (`34/35/64/65`)
- **#102: Scope scoring rubric specification (`scope-scoring-rubric.v1`)**
  - Added canonical rubric documentation: `docs/scope-scoring-rubric.md`
  - Added machine-readable rubric export: `scope_scoring_rubric()` in `src/specify_cli/scope_detection.py`
  - Added rubric payload schema validator: `validate_scope_scoring_rubric_payload(...)`
  - Added version-aware score band validation (`v1` enforces exactly 3 bands)
  - Added deeper rubric shape checks (score band item fields/types, unique dimension names)
  - Formalized deterministic tie-break and rationale-template rules for multi-channel consistency
  - Added rubric conformance tests in `tests/test_scope_detection.py`
- **#105: Stable gate consumption contract for CLI/TTY/API (`scope-gate-consumption.v1`)**
  - Added channel-agnostic contract module: `src/specify_cli/scope_gate_contract.py`
  - Added typed payload builders/normalizers:
    - `build_scope_gate_payload(...)`
    - `normalize_scope_gate_payload(...)`
    - `validate_scope_gate_payload(...)`
  - Added explicit error codes, strict validation mode, and deterministic fallback rules
  - Added contract documentation: `docs/scope-gate-consumption-contract.md`
  - Added contract test suite: `tests/test_scope_gate_contract.py`

### Changed

- **P007 (#15): Phase 0 scaffolding scripts (ideate, select, structure)**
  - New `ideate.sh` / `ideate.ps1`: scaffold `.spec-kit/ideas_backlog.md` with SCAMPER + HMW template (#15)
  - New `select.sh` / `select.ps1`: scaffold `.spec-kit/idea_selection.md` with AI-RICE scoring table (#15)
  - New `structure.sh` / `structure.ps1`: scaffold `.spec-kit/ai_vision_canvas.md` with 18-section canvas (#15)
  - All three scripts substitute `[PROJECT_NAME]` and `[ISO_8601_TIMESTAMP]` placeholders automatically (#15)
  - Idempotent: exit non-zero if artifact already exists; `--force` / `-Force` flag allows overwrite (#15)
  - `--help` / `-Help` prints usage with prerequisites and next-step guidance (#15)
  - 30 new pytest tests covering creation, idempotency, force, help, timestamp substitution, project name (#15)

- **P025 (#88): Self-update check and upgrade command for specify CLI**
  - New `specify update` command: checks for newer release, shows version diff, prompts to upgrade (#88)
  - `specify update --check`: scriptable flag — exits 0 if up-to-date, 1 if update available (#88)
  - `specify update --no-upgrade`: show update info without prompting to run upgrade (#88)
  - Passive notification at end of `specify check` when a newer version is cached (#88)
  - 24-hour cache (`platformdirs.user_data_dir("specify-cli") / "update_cache.json"`) avoids repeated API calls (#88)
  - Passive check respects `CI=true` and `SPECIFY_NO_UPDATE_CHECK=1` env vars; explicit `specify update` always proceeds (#88)
  - Upgrade command shown for both `uv` (primary) and `pip` (fallback) users (#88)
  - Network failures silently ignored — never crash main commands (#88)

  - Configurable model IDs via `env:` block (`REVIEW_MODEL`, `SUMMARY_MODEL`) — no hardcoded model strings (#77)
  - Configurable token limits via `env:` block (`MAX_REVIEW_TOKENS: 1500`, `MAX_SUMMARY_TOKENS: 800`) (#77)
  - Retry loop with exponential backoff (up to `MAX_RETRY` attempts, capped at `MAX_RETRY_SLEEP` seconds per sleep, default 30s) for both jobs (#77)
  - Non-empty / markdown-structure validation of model output with warning instead of hard failure (#77)
  - `::add-mask::` applied to `GH_MODELS_TOKEN` at step start to prevent accidental log exposure (#77)
  - Configurable `MAX_REVIEW_CHARS` (default 8000) and `MAX_SUMMARY_CHARS` (default 6000) via `env:` block (#76)
  - `truncated_at` output exposed — footer now shows exact truncation point and full diff size (#76)
  - `skip-ai-review` label support — add label to any PR to suppress both jobs (#76)
  - Model name shown dynamically in review/summary footer comments (#77)

- **P022 (#11, #12): Phase 0 + Strategy Toolkit integration in constitution template and SDD agent docs**
  - `templates/constitution-template.md`: Added `PHASE 0 INTEGRATION CHECK` comment block guiding derivation of principles from `.spec-kit/` (Phase 0) and `.ideas/` (Strategy Toolkit) artifacts
  - `.github/agents/speckit.constitution.agent.md`: Step 2 now discovers Phase 0 artifacts (`.spec-kit/`) and Strategy Toolkit artifacts (`.ideas/`) before falling back to README; added Execution Model clarification ("You are the executor")
  - `.github/agents/speckit.specify.agent.md`: Phase 0 context block referencing `.spec-kit/` and `.ideas/`
  - `.github/agents/speckit.plan.agent.md`: Phase 0 context block referencing `.spec-kit/` and `.ideas/`
  - `.github/agents/speckit.tasks.agent.md`: Phase 0 context block referencing `.spec-kit/` and `.ideas/`

- **P021 (#27): `--no-banner` flag for `specify init`** - Suppress ASCII art banner for CI/CD pipelines
  - Use `--no-banner` to skip the decorative banner when running in non-interactive environments
  - All init functionality remains intact — only the visual banner is suppressed
  - Works with `--dry-run`, `--here`, and all other flags

- **P020 (#26): `--dry-run` flag for `specify init`** - Preview what would be done without writing any files
  - Shows project name, target path, AI assistant, script type, template repo, and git init plan
  - Validates all inputs (agent, script type) before showing preview — invalid flags still error correctly
  - Works with `--here` flag for current-directory initialization
  - Does not download templates, create directories, or modify the filesystem

- **P015: Phase 0 onboarding integration** - Updated welcome message to show complete Phase 0 → SDD workflow
  - Phase 0 commands (`/speckit.ideate`, `/speckit.select`, `/speckit.structure`) now displayed in onboarding
  - Moved quality commands (`/speckit.clarify`, `/speckit.analyze`, `/speckit.checklist`) from "Enhancement Commands" to "Core SDD Workflow"
  - Auto-create `.gitignore` with security patterns for agent credentials:
    - `.github/agents/*.credentials.md`
    - `.specify/memory/*.sensitive.md`
  - Updated security notice to confirm automatic `.gitignore` protection
- **Upstream sync (2026-02-17)** - Integrated extension-system foundations from upstream:
  - `specify extension` command group and extension manager module
  - Extension docs/templates/test suite scaffolding
  - Antigravity (`agy`) agent support in CLI and packaging scripts
  - `constitution-template` initialization flow for new projects

### Changed

- **Script type choices now include platform labels**: `sh` → `"POSIX Shell (bash/zsh) [macOS/Linux]"`, `ps` → `"PowerShell [Windows]"` for clarity in interactive prompts (upstream #1379, Angie Byron)

### Fixed

- **P023 (#80): Fix DEFAULT_CATALOG_URL and catalog.json to point to fork nsalvacao/spec-kit**
  - `src/specify_cli/extensions.py`: `DEFAULT_CATALOG_URL` updated from `github/spec-kit` to `nsalvacao/spec-kit`
  - `extensions/catalog.json`: `catalog_url` field updated from `github/spec-kit` to `nsalvacao/spec-kit`
  - Ensures `specify extension search` fetches the fork's catalog by default

- **P004 (#25): Multi-agent `--ai` support** - `specify init --ai copilot,claude` now works correctly
  - Accepts comma-separated list of agents (e.g. `--ai copilot,claude,gemini`)
  - Validates all agents before starting; exits with clear error if any is invalid
  - Primary agent creates the project; extra agents overlay their templates into the same directory
  - Extra agent downloads are isolated — a failure does not abort the overall init
  - `precheck` and `ai-select` tracker steps now show all selected agents
  - Tests: 10 new unit/integration tests in `tests/test_multi_agent_init.py`
  - Created `scripts/python/state-update.py` for atomic YAML updates
  - Updated `state-log-violation.sh/ps1`, `state-reconstruct.sh/ps1`, and `state-check.sh/ps1` to use Python backend
  - Eliminates yq v3/v4 syntax breaking changes
  - Provides atomic, safe YAML updates without external dependency on yq
- **P002: state-init yq hard-dependency** - Removed spurious `yq` hard-dependency from `state-init.sh` and `state-init.ps1`
  - Both scripts only write static YAML via heredoc/Set-Content; yq was never invoked
  - Fixes init failure on systems without yq installed
- **P003 (#19): ripgrep not enforced at init** - `specify init` now checks for `rg` (ripgrep) and shows a
  prominent yellow warning panel when it is not installed.
  - Warning includes install instructions for Linux/macOS/Windows/Cargo
  - Initialisation continues (rg is not required for `init` itself, only for validator scripts)
  - `precheck` tracker step now reflects `rg` availability
  - Security hardening for extension installation/registration:
  - Validate command file paths remain inside extension directory
  - Validate command aliases/identifiers before writing generated files
  - Validate extension IDs used by catalog downloads
  - Use generated temporary ZIP filenames for `specify extension add --from`

### Changed

- **Dependencies**: yq is no longer required for state management (Python 3 with PyYAML is used instead)

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
