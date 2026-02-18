---
description: Execute the implementation plan by processing and executing all tasks defined in tasks.md
scripts:
  sh: scripts/bash/check-prerequisites.sh --json --require-tasks --include-tasks
  ps: scripts/powershell/check-prerequisites.ps1 -Json -RequireTasks -IncludeTasks
---

## Role

Execute the implementation plan defined in `tasks.md`, following TDD discipline and phase-by-phase task completion, tracking progress throughout.

## Context Inputs

| Artifact | Path | Required |
|----------|------|----------|
| User input | `$ARGUMENTS` | Optional — override or focus hint |
| Task list | `FEATURE_DIR/tasks.md` | ✅ Mandatory |
| Technical plan | `FEATURE_DIR/plan.md` | ✅ Mandatory |
| Data model | `FEATURE_DIR/data-model.md` | If exists |
| API contracts | `FEATURE_DIR/contracts/` | If exists |
| Research notes | `FEATURE_DIR/research.md` | If exists |
| Checklists | `FEATURE_DIR/checklists/` | If exists — checked before start |

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Execution Flow

1. **Bootstrap** — run `{SCRIPT}` from repo root; parse `FEATURE_DIR` and `AVAILABLE_DOCS`. All paths must be absolute.

2. **Check checklists** (if `FEATURE_DIR/checklists/` exists):
   - Count `- [ ]` (incomplete) and `- [x]` / `- [X]` (complete) per file
   - Display status table; if any checklist is incomplete, **ask before proceeding**

3. **Load context** — read `tasks.md`, `plan.md`, and any existing optional docs listed above.

4. **Verify project setup** — create or validate ignore files based on detected tech stack:
   - Git repo → `.gitignore`; Docker → `.dockerignore`; ESLint → `.eslintignore`; Prettier → `.prettierignore`; Terraform → `.terraformignore`
   - Append missing critical patterns to existing files; create with full pattern set if missing

5. **Parse task structure** from `tasks.md`:
   - Identify phases (Setup → Tests → Core → Integration → Polish)
   - Note dependencies and parallel markers `[P]`

6. **Execute phase-by-phase**:
   - Complete each phase before starting the next
   - **Tests before implementation** (TDD: RED → GREEN)
   - Run parallel `[P]` tasks concurrently; sequential tasks in order
   - After each completed task: mark `[x]` in `tasks.md` and report progress

7. **Validate completion**:
   - All tasks marked complete
   - Implemented features match specification
   - Tests pass; coverage meets requirements
   - Report final status with summary

## Input / Output Specification

**Input**: `tasks.md` + `plan.md` + optional design artifacts

**Output**:

| Artifact | Description |
|----------|-------------|
| Implemented code | Files defined in `tasks.md` / `plan.md` |
| Updated `tasks.md` | All completed tasks marked `[x]` |
| Progress reports | Inline after each phase |

## Error Scenarios

| Condition | Detection | Action |
|-----------|-----------|--------|
| `tasks.md` missing | Script reports `--require-tasks` failure | Halt — suggest running `/speckit.tasks` first |
| `plan.md` missing | Script reports missing `plan.md` | Halt — suggest running `/speckit.plan` first |
| Checklist incomplete | `- [ ]` items found | Ask user to confirm before proceeding |
| Sequential task fails | Non-zero exit / test failure | Halt execution; report error with context |
| Parallel task `[P]` fails | Failure in one parallel task | Continue remaining `[P]` tasks; report failures |
| Quote conflict in args | Single quotes in description | Escape: `'I'\''m Groot'` or use double quotes |

> If `tasks.md` is incomplete or missing, run `/speckit.tasks` first to generate the task list.
