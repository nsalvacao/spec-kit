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

## 8. Conclusion

This audit identified **10 high-severity discoverability gaps**
(3 runtime, 7 documentation) and fixed all of them. The `amend`
command is now fully discoverable across all surfaces: CLI runtime
(Next Steps panel), documentation (README, cli.md, walkthrough),
generated agent artifacts, and release packages.
