# Command Discoverability Audit

> Audit performed: 2025-02-26 | Related issue: #176

## Canonical Command Inventory

Source of truth: `templates/commands/*.md`

| # | Command | Type | Description |
|---|---------|------|-------------|
| 1 | `ideate` | Phase 0 | Generate ideas backlog (SCAMPER + HMW) |
| 2 | `select` | Phase 0 | AI-RICE scoring and selection |
| 3 | `structure` | Phase 0 | AI vision canvas + vision brief |
| 4 | `validate` | Phase 0 | Gate G0 validation |
| 5 | `constitution` | Core SDD | Project governance principles |
| 6 | `specify` | Core SDD | Feature specification |
| 7 | `clarify` | Optional | Pre-implementation spec clarification |
| 8 | `plan` | Core SDD | Technical plan with stack and architecture |
| 9 | `tasks` | Core SDD | Task decomposition from plan |
| 10 | `implement` | Core SDD | Execute tasks according to plan |
| 11 | `amend` | Optional | Post-implementation spec amendment |
| 12 | `analyze` | Optional | Cross-artifact consistency check |
| 13 | `checklist` | Optional | Quality checklist generation |
| 14 | `taskstoissues` | Optional | Convert tasks to GitHub issues |

## Audit Matrix (Command × Surface)

Legend: ✅ Present | ❌ Missing (before fix) | ➕ Added by this audit | ➖ N/A

| Command | templates/ | README | cli | walkthrough | spec-driven | Release | CLI |
|---------|:----------:|:------:|:---:|:-----------:|:-----------:|:-------:|:---:|
| ideate | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| select | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| structure | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| validate | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| constitution | ✅ | ✅ | ✅ | ✅ | ➖ | ✅ | ✅ |
| specify | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| clarify | ✅ | ✅ | ✅ | ✅ | ➖ | ✅ | ✅ |
| plan | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| tasks | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| implement | ✅ | ✅ | ✅ | ✅ | ➖ | ✅ | ✅ |
| amend | ✅ | ❌ ➕ | ❌ ➕ | ❌ ➕ | ➖ | ✅ | ✅ |
| analyze | ✅ | ✅ | ✅ | ✅ | ➖ | ✅ | ✅ |
| checklist | ✅ | ✅ | ✅ | ❌ ➕ | ➖ | ✅ | ✅ |
| taskstoissues | ✅ | ✅ | ❌ ➕ | ❌ ➕ | ➖ | ✅ | ✅ |

## Gap List

### High Severity (Fixed)

| Gap | Surface | Status |
|-----|---------|--------|
| `amend` missing from README.md SDD command list | README.md | ✅ Fixed |
| `amend` missing from README.md quick-start helpers | README.md | ✅ Fixed |
| `amend` missing from CLI reference | docs/cli.md | ✅ Fixed |
| `amend` missing from walkthrough | docs/walkthrough.md | ✅ Fixed |
| `taskstoissues` missing from CLI reference | docs/cli.md | ✅ Fixed |
| `taskstoissues` missing from walkthrough | docs/walkthrough.md | ✅ Fixed |
| `checklist` missing from walkthrough | docs/walkthrough.md | ✅ Fixed |
| `amend` missing from docs-site CLI ref | docs-site/docs/cli.md | ✅ Fixed |
| `amend` missing from docs-site walkthrough | docs-site/docs/walkthrough.md | ✅ Fixed |
| `taskstoissues` missing from docs-site CLI ref | docs-site/docs/cli.md | ✅ Fixed |
| `taskstoissues` missing from docs-site walkthrough | docs-site/docs/walkthrough.md | ✅ Fixed |
| `checklist` missing from docs-site walkthrough | docs-site/docs/walkthrough.md | ✅ Fixed |

### Low Severity (Informational)

| Gap | Surface | Notes |
|-----|---------|-------|
| Phase 0 + core SDD subset only | spec-driven.md | By design — theory doc |
| No command references | methodology.md | By design — theory only |
| Not in instruction-contract set | template_instruction_contract.py | Core pipeline only |
| Not in handoff-metadata mapping | handoff_metadata_lint.py | Stage-mapped only |

## Release Package Coverage

Release scripts (`create-release-packages.sh` and `.ps1`) use dynamic
glob patterns (`templates/commands/*.md`) to discover all command templates.
All 14 commands are automatically included in release packages without
requiring explicit enumeration.

## CI/Validation Opportunities

To prevent future regressions where new commands are added as templates
but not reflected in documentation surfaces:

1. **Template-to-docs sync check**: A CI step could compare
   `ls templates/commands/*.md` against command references in README.md
   and docs/cli.md.
2. **Command count assertion**: A test could assert that the number of
   commands in docs/cli.md matches the count of files in
   `templates/commands/`.

## Conclusion

The `amend` command was fully implemented as a template but absent from
all user-facing documentation surfaces. This audit identified and fixed
seven documentation gaps, bringing all 14 commands to full discoverability
across the primary documentation surfaces (README.md, docs/cli.md,
docs/walkthrough.md).
