# Command Discoverability Audit

> Audit performed: 2026-02-26 | Related issue: #176

## 1. Canonical Command Inventory

Source of truth: `templates/commands/*.md` (14 commands)

| # | Identifier | Display Name | Type | Description |
|---|------------|-------------|------|-------------|
| 1 | `ideate` | `/speckit.ideate` | Phase 0 | Generate ideas (SCAMPER + HMW) |
| 2 | `select` | `/speckit.select` | Phase 0 | AI-RICE scoring and selection |
| 3 | `structure` | `/speckit.structure` | Phase 0 | Integrated Canvas + vision brief |
| 4 | `validate` | `/speckit.validate` | Phase 0 | Gate G0 validation |
| 5 | `constitution` | `/speckit.constitution` | Core SDD | Project governance principles |
| 6 | `specify` | `/speckit.specify` | Core SDD | Feature specification |
| 7 | `clarify` | `/speckit.clarify` | Core SDD | Clarify spec ambiguities |
| 8 | `plan` | `/speckit.plan` | Core SDD | Technical plan |
| 9 | `tasks` | `/speckit.tasks` | Core SDD | Task decomposition |
| 10 | `implement` | `/speckit.implement` | Core SDD | Execute tasks |
| 11 | `amend` | `/speckit.amend` | Optional | Post-implementation spec amendment |
| 12 | `analyze` | `/speckit.analyze` | Optional | Cross-artifact consistency |
| 13 | `checklist` | `/speckit.checklist` | Optional | Quality checklist generation |
| 14 | `taskstoissues` | `/speckit.taskstoissues` | Optional | Convert tasks to GitHub issues |

No orphaned, duplicated, or inconsistently named commands found.
All identifiers map 1:1 to template filenames (`<id>.md`) and to runtime
display names (`/speckit.<id>`). No aliases exist.

## 2. Audit Matrix (Command × Surface)

### Surface Definitions

| Surface | Description |
|---------|-------------|
| Templates | `templates/commands/*.md` source files |
| Next Steps | CLI panel shown after `specify init` |
| `--help` | `specify --help` output (CLI commands only) |
| README | `README.md` command listings |
| cli.md | `docs/cli.md` + `docs-site/docs/cli.md` |
| Walkthrough | `docs/walkthrough.md` + `docs-site/docs/walkthrough.md` |
| Release pkgs | `.github/workflows/scripts/create-release-packages.sh` |
| Gen. artifacts | Agent command files (e.g. `.github/agents/`) |

### Matrix

Legend: ✅ Pass | ❌ Fail → ➕ Fixed | ➖ N/A

| Command | Templates | Next Steps | --help | README | cli.md | Walk | Release | Artifacts |
|---------|:---------:|:----------:|:------:|:------:|:------:|:----:|:-------:|:---------:|
| ideate | ✅ | ✅ | ➖ | ✅ | ✅ | ✅ | ✅ | ✅ |
| select | ✅ | ✅ | ➖ | ✅ | ✅ | ✅ | ✅ | ✅ |
| structure | ✅ | ✅ | ➖ | ✅ | ✅ | ✅ | ✅ | ✅ |
| validate | ✅ | ❌ ➕ | ➖ | ✅ | ✅ | ✅ | ✅ | ✅ |
| constitution | ✅ | ✅ | ➖ | ✅ | ✅ | ✅ | ✅ | ✅ |
| specify | ✅ | ✅ | ➖ | ✅ | ✅ | ✅ | ✅ | ✅ |
| clarify | ✅ | ✅ | ➖ | ✅ | ✅ | ✅ | ✅ | ✅ |
| plan | ✅ | ✅ | ➖ | ✅ | ✅ | ✅ | ✅ | ✅ |
| tasks | ✅ | ✅ | ➖ | ✅ | ✅ | ✅ | ✅ | ✅ |
| implement | ✅ | ✅ | ➖ | ✅ | ✅ | ✅ | ✅ | ✅ |
| amend | ✅ | ❌ ➕ | ➖ | ❌ ➕ | ❌ ➕ | ❌ ➕ | ✅ | ✅ |
| analyze | ✅ | ✅ | ➖ | ✅ | ✅ | ❌ ➕ | ✅ | ✅ |
| checklist | ✅ | ✅ | ➖ | ✅ | ✅ | ❌ ➕ | ✅ | ✅ |
| taskstoissues | ✅ | ❌ ➕ | ➖ | ✅ | ❌ ➕ | ❌ ➕ | ✅ | ✅ |

Note: `--help` is marked N/A because slash commands are agent commands,
not CLI sub-commands. The `specify --help` surface lists CLI commands
(`init`, `check`, `version`, etc.) which are a separate surface.

## 3. Runtime UX Validation

### 3.1 `specify --help` (main screen)

CLI commands displayed: `init`, `check`, `version`, `hierarchy-contract`,
`scope-detect`, `scope-gate`, `update`, `extension`.

Slash commands are not part of this surface (by design). They are
delivered through agent-specific command files and the "Next Steps"
panel after `specify init`.

### 3.2 `specify init` — Next Steps panel

After running `specify init /tmp/test --ai copilot --script sh --no-git`:

```text
Phase 0: AI System Ideation
• /speckit.ideate - Generate ideas using SCAMPER + HMW
• /speckit.select - Score and select best idea using AI-RICE
• /speckit.structure - Complete Integrated Canvas and vision brief
• /speckit.validate - Run Gate G0 validation

Core SDD Workflow
• /speckit.constitution - Establish project principles
• /speckit.specify - Create baseline specification
• /speckit.clarify - Clarify and de-risk spec ambiguities
• /speckit.plan - Create implementation plan
• /speckit.tasks - Generate actionable tasks
• /speckit.implement - Execute implementation
• /speckit.amend - Amend spec post-implementation

Optional Quality Helpers
• /speckit.analyze - Check cross-artifact alignment
• /speckit.checklist - Validate requirements completeness
• /speckit.taskstoissues - Convert tasks to GitHub issues
```

All 14 commands present. Ordering follows canonical workflow sequence.
`amend` appears in logical position after `implement`.

### 3.3 Generated agent artifacts

Validated for `--ai copilot` (GitHub Copilot agent files):

```text
.github/agents/speckit.amend.agent.md        ✅
.github/agents/speckit.analyze.agent.md       ✅
.github/agents/speckit.checklist.agent.md     ✅
.github/agents/speckit.clarify.agent.md       ✅
.github/agents/speckit.constitution.agent.md  ✅
.github/agents/speckit.ideate.agent.md        ✅
.github/agents/speckit.implement.agent.md     ✅
.github/agents/speckit.plan.agent.md          ✅
.github/agents/speckit.select.agent.md        ✅
.github/agents/speckit.specify.agent.md       ✅
.github/agents/speckit.structure.agent.md     ✅
.github/agents/speckit.tasks.agent.md         ✅
.github/agents/speckit.taskstoissues.agent.md ✅
.github/agents/speckit.validate.agent.md      ✅
```

All 14 agent files generated. Release scripts use dynamic glob
(`templates/commands/*.md`), so all agents receive all commands
automatically.

## 4. Naming Consistency

| Surface | Identifier format | Consistent |
|---------|------------------|:----------:|
| Template files | `amend.md` | ✅ |
| Agent command files | `speckit.amend.agent.md` | ✅ |
| CLI "Next Steps" | `/speckit.amend` | ✅ |
| README.md | `/speckit.amend` | ✅ |
| docs/cli.md | `/speckit.amend` | ✅ |
| docs/walkthrough.md | `/speckit.amend` | ✅ |

No divergence between runtime UX and documentation terminology.
No aliases in use.

## 5. Gap List

### High Severity (All Fixed)

| # | Gap | Surface | Impact | Status |
|---|-----|---------|--------|--------|
| 1 | `amend` absent from Next Steps panel | CLI runtime | Users never see amend after init | ✅ Fixed |
| 2 | `validate` absent from Next Steps panel | CLI runtime | Phase 0 incomplete in UX | ✅ Fixed |
| 3 | `taskstoissues` absent from Next Steps | CLI runtime | Undiscoverable after init | ✅ Fixed |
| 4 | `amend` absent from README.md | Documentation | Not in main project docs | ✅ Fixed |
| 5 | `amend` absent from docs/cli.md | Documentation | Not in CLI reference | ✅ Fixed |
| 6 | `amend` absent from walkthrough | Documentation | Not in guided flow | ✅ Fixed |
| 7 | `taskstoissues` absent from cli.md | Documentation | Not in CLI reference | ✅ Fixed |
| 8 | `taskstoissues` absent from walkthrough | Documentation | Not in guided flow | ✅ Fixed |
| 9 | `checklist` absent from walkthrough | Documentation | Not in guided flow | ✅ Fixed |
| 10 | Next Steps ordering wrong | CLI runtime | clarify before specify | ✅ Fixed |

Fixes also mirrored in `docs-site/docs/cli.md` and
`docs-site/docs/walkthrough.md`.

### Low Severity (Informational — By Design)

| Gap | Surface | Rationale |
|-----|---------|-----------|
| Subset only in spec-driven.md | spec-driven.md | Theory document, not reference |
| No commands in methodology.md | methodology.md | Theory document |
| amend not in contract validation | template_instruction_contract.py | Validates core pipeline only |
| amend not in handoff-metadata lint | handoff_metadata_lint.py | Stage-mapped templates only |

## 6. Release Package Coverage

Release scripts use dynamic glob patterns:

- **Bash**: `for template in templates/commands/*.md` (line 47)
- **PowerShell**: `Get-ChildItem -Path "templates/commands/*.md"` (line 81)

All 14 commands automatically included. No manual enumeration needed.

## 7. Regression Prevention

### Concrete proposals

1. **Next Steps snapshot test**: Add a pytest test that imports the
   "Next Steps" lines from `__init__.py` and asserts all 14 template
   names appear. Catches drift between templates and CLI output.

2. **Template-to-docs sync CI check**: A workflow step that compares
   `ls templates/commands/*.md | wc -l` against the count of
   `/speckit.*` references in docs/cli.md. Fails on mismatch.

3. **Generated artifact assertion**: The existing
   `test_phase0_constitution_integration.py` pattern can be extended
   to assert that all template commands produce corresponding agent
   files in generated output.

## 8. Functional Validation

### 8.1 Runtime behavior vs. user intent

Each command highlighted in this audit was validated by inspecting the
generated agent file content against the Next Steps panel description.

| Command | Panel text | Template promise | Match |
|---------|-----------|-----------------|:-----:|
| amend | Amend spec post-implementation | Amend a completed feature specification with new edge cases... cascade through existing tests and implementation | ✅ |
| validate | Run Gate G0 validation | Execute Gate G0 checks and produce a validation report | ✅ |
| taskstoissues | Convert tasks to GitHub issues | Convert existing tasks into actionable, dependency-ordered GitHub issues | ✅ |

### 8.2 Sufficiency of user-facing information

- All 14 commands include a short description in the Next Steps panel.
- Each generated agent file (`speckit.*.agent.md`) contains a full
  `description` in YAML frontmatter, matching the template source.
- The `amend` template includes "When to Use" / "When NOT to Use"
  guidance and references to related commands (`/speckit.clarify`,
  `/speckit.specify`, `/speckit.constitution`).
- A first-time user can determine which command to invoke based on the
  panel descriptions and grouping alone (Phase 0 → Core SDD → Optional).

### 8.3 What was validated empirically

- `specify --help` output captured — CLI commands listed.
- `specify version` output captured — CLI version `0.0.53`,
  Template version `0.0.66`.
- `specify init --ai copilot` executed — Next Steps panel captured
  showing all 14 commands with correct grouping and ordering.
- All 14 generated agent files verified present in output directory.
- Agent file content inspected for `amend`, `validate`, `taskstoissues`:
  YAML frontmatter, script references, and workflow instructions confirmed.
- Version coherence check (`version-orchestrator.py check`) passed.

### 8.4 What was NOT validated empirically

- Actual agent invocation (running `/speckit.amend` in an AI agent
  session) — this requires an active AI agent connection, out of scope
  for a CI-reproducible audit.
- Multi-agent generation (only `--ai copilot` was tested; other agents
  use the same glob-based generation path and are expected to behave
  identically).
- PowerShell script variant generation (`--script ps`) — not tested
  in this environment but uses the same template engine.

## 9. UX Semantics and Workflow Clarity

### 9.1 Command self-explanation in context

The Next Steps panel groups commands into three sections:

1. **Phase 0: AI System Ideation** — 4 commands that progress linearly
   (ideate → select → structure → validate). Each description starts
   with a verb that implies the next logical step.

2. **Core SDD Workflow** — 7 commands following the SDD pipeline.
   `specify` and `clarify` are adjacent with distinct verbs ("Create
   baseline specification" vs "Clarify and de-risk spec ambiguities").
   `amend` follows `implement` with the qualifier "post-implementation"
   to clarify its trigger condition.

3. **Optional Quality Helpers** — 3 utility commands clearly separated
   from the core workflow. Their descriptions start with action verbs
   specific to their purpose (Check, Validate, Convert).

### 9.2 Differentiation between similar commands

| Pair | Distinction | Clear? |
|------|------------|:------:|
| specify vs clarify | "Create baseline" vs "Clarify and de-risk" | ✅ |
| clarify vs amend | "Clarify ... ambiguities" (pre-implementation) vs "Amend spec post-implementation" | ✅ |
| checklist vs analyze | "Validate requirements completeness" vs "Check cross-artifact alignment" | ✅ |
| tasks vs taskstoissues | "Generate actionable tasks" vs "Convert tasks to GitHub issues" | ✅ |

### 9.3 Cognitive load assessment

- 14 commands split across 3 groups reduces scanning burden.
- Phase progression is top-to-bottom (Phase 0 first, then SDD, then
  optional) matching the expected user journey.
- The "Optional" label on the third group prevents users from thinking
  all 14 commands are mandatory.

## 10. Versioning and Release Coherence

### 10.1 Version consistency check

| Surface | Version | Status |
|---------|---------|:------:|
| `pyproject.toml` | 0.0.53 | ✅ |
| `uv.lock` | 0.0.53 | ✅ |
| `specify version` runtime | 0.0.53 | ✅ |
| `CHANGELOG.md` `[0.0.53]` heading | Present | ✅ |
| `CHANGELOG.md` `[Unreleased]` | Contains #176 changes | ✅ |
| `version-orchestrator.py check` | `"ok": true` | ✅ |

### 10.2 Version bump rationale

The version was initially bumped to `0.0.54` in this PR but has been
**reverted to `0.0.53`** because:

- The version-coherence check (`version-orchestrator.py check`) requires
  that a version declared in `pyproject.toml` has a matching release
  heading (`## [X.Y.Z] - YYYY-MM-DD`) in CHANGELOG.md.
- PR changes should go under `[Unreleased]`; the release workflow
  (`release.yml` + `get-next-version.sh`) handles version bumping from
  git tags at release time.
- Bumping the package version in a feature PR would require also creating
  a release heading, which conflicts with the project's automated release
  workflow.

### 10.3 Release tag vs package version

The project uses a dual-version model:

- **Git tag / release version** (`v0.0.66`): auto-incremented by
  `get-next-version.sh` from the latest git tag on each release.
- **Package version** (`0.0.53`): declared in `pyproject.toml`, bumped
  via `version-orchestrator.py bump` when merging to main.

These are intentionally separate. No stale version references found.

## 11. Packaging and Distribution

### 11.1 Release artifact content

The release package scripts (`create-release-packages.sh` and `.ps1`)
use dynamic glob patterns to discover templates:

```bash
for template in templates/commands/*.md; do
```

This guarantees that any new template in `templates/commands/` is
automatically included in all release packages for all agents, without
requiring manual updates to the scripts.

### 11.2 Installation path consistency

A user installing the released version receives:

- The updated Next Steps panel (defined in `__init__.py`, packaged
  with the Python wheel).
- The corrected command set (14 commands in all 3 groups).
- All 14 agent command files (generated from templates at init time).

No divergence between source, package, and runtime behavior.

## 12. Scope Declaration

### Validated

- CLI runtime surfaces (`--help`, `version`, `init` Next Steps panel)
- Generated agent files (copilot, via `--ai copilot`)
- Documentation surfaces (README, cli.md, walkthrough, docs-site mirrors)
- Release script glob coverage
- Version coherence across pyproject.toml, uv.lock, CHANGELOG.md, runtime
- Naming consistency (template → agent file → panel → docs)
- UX semantics (grouping, ordering, description clarity)

### Not validated (out of scope)

- Live AI agent invocation of `/speckit.amend` (requires agent session)
- Multi-agent generation (`--ai claude`, `--ai gemini`, etc.)
- PowerShell script variant (`--script ps`)
- Upstream (github/spec-kit) divergence analysis

### Assumptions

- Other agents use the same template glob path and will receive
  identical command files.
- PowerShell release script uses the same glob pattern as bash.
- The `version-orchestrator.py check` tool is the authoritative
  version-coherence gate.

## 13. Conclusion

This audit identified **10 high-severity discoverability gaps**
(3 runtime, 7 documentation) and fixed all of them. The `amend`
command is now fully discoverable across all surfaces: CLI runtime
(Next Steps panel), documentation (README, cli.md, walkthrough),
generated agent artifacts, and release packages.

Version coherence is verified green. The version bump was reverted
to maintain alignment with the project's automated release workflow.
All version-related tests pass because the system is coherent.
