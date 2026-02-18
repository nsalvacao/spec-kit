---
description: Convert existing tasks into actionable, dependency-ordered GitHub issues for the feature based on available design artifacts.
tools: ['github/github-mcp-server/issue_write']
scripts:
  sh: scripts/bash/check-prerequisites.sh --json --require-tasks --include-tasks
  ps: scripts/powershell/check-prerequisites.ps1 -Json -RequireTasks -IncludeTasks
---

## Role

Convert the task list in `tasks.md` into well-structured, dependency-ordered GitHub issues, one issue per task, in the correct repository.

## Context Inputs

| Artifact | Path | Required |
|----------|------|----------|
| User input | `$ARGUMENTS` | Optional — label or milestone override |
| Task list | `FEATURE_DIR/tasks.md` | ✅ Mandatory |
| Technical plan | `FEATURE_DIR/plan.md` | If exists — for context |
| Feature spec | `FEATURE_DIR/spec.md` | If exists — for description enrichment |

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Execution Flow

1. **Bootstrap** — run `{SCRIPT}` from repo root; parse `FEATURE_DIR` and task file path.

2. **Verify GitHub remote**:

   ```bash
   git config --get remote.origin.url
   ```

   > ⛔ **STOP** if the remote is not a GitHub URL — do not create issues in any other host.

3. **Confirm target repository** — extract `owner/repo` from the remote URL; display it and ask user to confirm before creating any issue.

4. **Parse `tasks.md`** — extract tasks in dependency order:
   - Task ID, title, description, phase, dependencies, parallel marker `[P]`
   - Preserve dependency links between tasks for issue cross-references

5. **Create GitHub issues** — one issue per task using the GitHub MCP server:
   - Title: task title
   - Body: task description + dependency list (reference related issues by number after creation)
   - Labels: phase label (e.g., `phase:setup`, `phase:core`) + `auto-generated`
   - Milestone: from `$ARGUMENTS` if provided
   - Create in dependency order so earlier issues exist when cross-referenced

6. **Report completion** — list created issue numbers and URLs; note any failures.

## Input / Output Specification

**Input**: `tasks.md` (required), `plan.md` / `spec.md` (optional enrichment)

**Output**:

| Artifact | Description |
|----------|-------------|
| GitHub issues | One issue per task, in dependency order |
| Creation report | Issue numbers, titles, and URLs |

## Error Scenarios

| Condition | Detection | Action |
|-----------|-----------|--------|
| `tasks.md` missing | Script `--require-tasks` fails | Halt — suggest running `/speckit.tasks` first |
| Remote is not GitHub | URL does not match `github.com` | ⛔ Halt — never create issues on non-GitHub remotes |
| Wrong repository confirmed | User rejects target repo | Halt — ask user to clarify the correct remote |
| Issue creation fails | MCP server error | Report failure; continue with remaining tasks |
| No tasks found | `tasks.md` is empty or malformed | `ERROR "No tasks found in tasks.md"` — halt |

> ⚠️ **NEVER create issues in repositories that do not match the remote URL.**

## Examples

**Good task → issue mapping**:

```markdown
# Input task
- [T1] Set up project structure (Phase: Setup)

# Output issue
Title: "Set up project structure"
Labels: ["phase:setup", "auto-generated"]
Body: "Initialize directories, config files, and dependencies as defined in plan.md."
```

**Bad** (do not do this):

- Creating a single issue for multiple tasks
- Skipping dependency ordering
- Creating issues without confirming the target repository
