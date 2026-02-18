# Spec Kit - Copilot Instructions

This repository is an independent fork of `github/spec-kit` with **Phase 0: AI System Ideation** integrated before the standard Spec-Driven Development (SDD) workflow.

**Spec Kit** is a comprehensive toolkit for implementing Spec-Driven Development - a methodology that emphasizes creating clear specifications before implementation. The toolkit includes templates, scripts, and workflows that guide development teams through a structured approach to building software.

**Specify CLI** is the command-line interface that bootstraps projects with the Spec Kit framework, setting up necessary directory structures, templates, and AI agent integrations.

---

## Agent Operating System

### Toolbox Available in This Environment

The following tools, skills, agents, and plugins are available to Copilot agents working on this repository. Use them proactively — don't wait to be asked.

#### Slash Commands (Built-in)

| Command | When to Use |
|---------|-------------|
| `/plan` | Before any non-trivial task — create an implementation plan |
| `/diff` | Review changes before committing |
| `/review` | Run code review on staged/unstaged changes |
| `/compact` | When context window exceeds ~50% — summarize to free tokens |
| `/fleet` | Enable parallel subagent execution for independent tasks |
| `/tasks` | View and manage background agent tasks |
| `/agent` | Switch to a specialized agent (speckit, python-pro, etc.) |
| `/skills` | Manage and invoke skills |
| `/session` | Show session info and workspace summary |
| `/context` | Check context window token usage |

#### Specialist Agents (`/agent` → select)

| Agent | Use For |
|-------|---------|
| `speckit` | SDD/Phase 0 workflows, spec/plan/tasks generation |
| `python-pro` | CLI code changes in `src/specify_cli/__init__.py` |
| `test-engineer` | Writing/expanding pytest tests |
| `architect` | Architecture decisions, new feature design |
| `devops` | CI/CD fixes, GitHub Actions, release workflows |
| `security-expert` | Security reviews, dependency audits |

#### Skills (`/skills` → enable)

| Skill | Purpose | When to Use |
|-------|---------|-------------|
| `memory-systems` | Cross-session knowledge graph and entity persistence | Start every session; persist findings |
| `agentic-backlog-orchestrator` | Break backlog into parallelizable tasks for agents | When decomposing issues into tasks |
| `delegation-automation` | Delegate atomic tasks to CLI agents (85% token savings) | Boilerplate, CRUD, tests, docs |
| `deep-codebase-analysis` | Safe feature implementation and impact scoring | Before any large refactor |
| `multi-agent-patterns` | Coordinate parallel agent execution | Complex multi-file changes |
| `context-compression` | Structured context summarization | Context > 50% |
| `context-optimization` | KV-cache partitioning, token budgeting | Long sessions |
| `evaluation` | LLM-as-judge for agent output quality | After delegated tasks complete |
| `speckit-phase0` | Phase 0 AI Ideation workflow (built into this repo) | New features, strategic decisions |
| `speckit-setup` | Verify/initialize spec-kit in a project | New project onboarding |

#### Installed Plugins

These plugins are installed at `~/.copilot/installed-plugins/nsalvacao-claude-code-plugins/`.

**`productivity` plugin** — Task management and workplace memory

| Command | What It Does |
|---------|--------------|
| `/productivity:start` | Initialize `TASKS.md`, `CLAUDE.md`, `memory/`, open dashboard |
| `/productivity:update` | Triage stale tasks, sync external tools |
| `/productivity:update --comprehensive` | Deep scan — flag missed todos, enrich memory |

Skills: `task-management` (shared `TASKS.md`), `memory-management` (two-tier: `CLAUDE.md` hot cache + `memory/` deep storage).

> **Use at session start**: Run `/productivity:start` to initialize task tracking and reload memory context from previous sessions.

**`product-management` plugin** — Full PM workflow

| Command | What It Does |
|---------|--------------|
| `/write-spec` | Write a PRD/feature spec from a problem statement |
| `/roadmap-update` | Create or reprioritize the roadmap |
| `/stakeholder-update` | Generate exec/team updates |
| `/synthesize-research` | Synthesize user research into insights |

Skills: `feature-spec`, `roadmap-management` (RICE/MoSCoW/OKR), `stakeholder-comms`, `metrics-tracking`.

> **Use for**: Writing specs for issues before implementation, roadmap decisions, prioritization using AI-RICE (already used in Phase 0 of this project).

**`repo-structure` plugin** — Repository quality and compliance

| Command | What It Does |
|---------|--------------|
| `/repo-audit` | Non-destructive quality check (0-100 score across docs, security, CI/CD, community) |
| `/repo-setup` | Scaffold or upgrade repository structure |
| `/repo-improve --category=X` | Targeted improvements (security, docs, ci, community) |
| `/repo-validate` | Fast structure validation |

Skills: `quality-scoring`, `tech-stack-detection`, `compliance-standards`, `automation-strategies`.

> **Use for**: Periodic audits, checking if new workflows are needed, compliance checks.

**`strategy-toolkit` plugin** — Strategic thinking and execution planning

| Command | What It Does |
|---------|--------------|
| `/brainstorm` | Structured ideation with SCAMPER, Blue Ocean, JTBD, Flywheel |
| `/execution-plan` | Second-order planning, risk register, operationalized roadmap |
| `/strategic-review` | Pre-launch quality and readiness assessment |

Outputs saved to `.ideas/` (gitignored). Skills: `strategic-analysis` (12 frameworks).

> **Use for**: New feature strategy, upstream PR evaluation, Phase 0 ideation complement.

### Persistent Memory Protocol

To maintain continuity between sessions and agents:

1. **Session start**: Run `/productivity:start` — reloads `TASKS.md` + `CLAUDE.md` context
2. **During work**: Use `memory-systems` skill to store findings in knowledge graph
3. **Task tracking**: All tasks MUST be tracked in `TASKS.md` AND in the session SQL `todos` table
4. **Session end**: Update `TASKS.md` with completed/in-progress items; note blockers

Memory files for this project:

- `TASKS.md` (project root, gitignored) — active task board
- `CLAUDE.md` (project root, gitignored) — hot memory cache
- `memory/` (project root, gitignored) — deep memory (people, projects, glossary)
- `.ideas/` (project root, gitignored) — strategy artifacts

---

## Standard Development Workflow (The Loop)

Every agent MUST follow this **10-step cycle** for every task:

### Step 1 — PLAN

Analyze the request using sequential thinking. Before touching any file:

- Read relevant source files (use `grep` before `view`)
- Check `TASKS.md` for related work in progress
- Use `deep-codebase-analysis` skill for non-trivial changes
- Use `/plan` command for multi-file or complex changes

### Step 2 — DEFINE TODOs

Break work into atomic, independently completable steps:

- Add each step to `TASKS.md` under **Active**
- Assign `[PhX]` prefix matching issue taxonomy (Ph0=blocker, Ph1=core, Ph2=automation, Ph3=integration, Ph4=quality, Ph5=UX, Ph6=backlog)
- Record in session SQL `todos` table with `status='in_progress'` before starting

### Step 3 — TDD: Write Tests First (RED state)

For Python changes (`src/specify_cli/`), write failing tests **before** implementation:

```bash
uv run pytest tests/ -x --tb=short   # Confirm tests fail as expected
```

For bash scripts, write E2E test scenario in `scripts/bash/test-e2e-*.sh` before the script itself.

### Step 4 — DEVELOP (GREEN state)

Write **minimal** code to pass the tests:

- Python: follow PEP 8, use `pathlib.Path`, type hints, Rich for output
- Bash: `#!/usr/bin/env bash`, `set -euo pipefail`, source `common.sh`
- PowerShell: always create an equivalent `.ps1` when adding/modifying `.sh`
- Never change unrelated code
- `AGENT_CONFIG` in `__init__.py` is the single source of truth for agent metadata

### Step 5 — TEST + ITERATE (REFACTOR state)

```bash
uv run pytest tests/ --tb=short          # Full test suite
npx markdownlint-cli2 "**/*.md"          # Markdown lint
uv run specify check                     # CLI self-check
```

Add edge cases, check error paths, ensure robustness.

### Step 6 — VERIFY GLOBAL CONSISTENCY

```bash
uv run pytest tests/ -v                  # All 48+ tests must pass
uv run specify --help                    # CLI must be responsive
```

No regressions allowed. If tests fail in unrelated areas, investigate before proceeding.

### Step 7 — E2E VALIDATE

Validate the change works end-to-end in a real project context:

```bash
# Test CLI init with affected agent(s)
uv run specify init /tmp/test-speckit --ai <affected-agent>

# Verify generated structure
ls /tmp/test-speckit/

# Test release packages if scripts changed
./.github/workflows/scripts/create-release-packages.sh v1.0.0-test
ls .genreleases/
```

Verify output quality against the project's main goal. If quality is insufficient, return to Step 5 or defer with a new issue.

### Step 8 — MARK TASK DONE

```bash
# In TASKS.md: change [ ] to [x] and move to Done section
# In SQL: UPDATE todos SET status='done' WHERE id='X'
# If GitHub issue: add comment with summary of changes
```

### Step 9 — ATOMIC COMMIT

```bash
git add <only related files>
git commit -m "<type>(<scope>): <description>

<body if needed>

Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>"
```

Commit types: `fix`, `feat`, `refactor`, `test`, `docs`, `chore`, `ci`.
One logical change per commit. Never commit `.genreleases/`, `dashboard.html`, `.ideas/`.

### Step 10 — PUSH + PR + WAIT

```bash
git push origin <branch>
gh pr create --title "<type>: <description>" --body "<context>"
```

- One PR per logical change
- Wait for GitHub Actions (Lint, AI Review, Copilot Review)
- Do not merge until all checks pass
- For intake PRs: follow the 7-step upstream intake workflow in `AGENTS.md`

---

## Issue Triage Priority

When choosing what to work on, apply this order:

| Priority | Phase | What |
|----------|-------|------|
| 🔴 P0 | Ph0 | Blockers — must fix before anything else (e.g., broken state scripts) |
| 🔴 P1 | Ph1 | Core enablers — bugs that break the main CLI flow |
| 🟠 P2 | Ph2–Ph3 | Automation and integration work |
| 🟡 P3 | Ph4–Ph5 | Quality and UX improvements |
| ⚪ P4 | Ph6 | Backlog — future enhancements |

**Quick-wins** (label `quick-win`) can be pulled into any phase — they are small, high-impact changes. Prefer them when blocked on serial phases.

---

## CI/CD and Release Notes

### Active Workflows

| Workflow | Status | Trigger |
|----------|--------|---------|
| `lint.yml` | ✅ Healthy | Push/PR — runs `markdownlint-cli2` |
| `docs.yml` | ✅ Healthy | Push to `main` (`docs-site/**`) |
| `stale.yml` | ✅ Healthy | Daily cron — marks stale after 150d |
| `ai-review.yml` | ✅ Active | PR — GPT-4.1 AI review via actions-hub |
| `ai-triage.yml` | ✅ Active | Issues — GPT-4.1-mini automatic triage |
| `test.yml` | ✅ Active | Push/PR — uv run pytest |
| `release.yml` | ✅ Active | Push to `main` — semantic versioning (v0.0.26) |

### Known CI Status

All workflows are healthy as of v0.0.26. The following were fixed:
- `release.yml` — versioning script fixed (47de07e)
- `test.yml` — added pytest CI (47de07e); `uv.lock` tracked (5845dac)
- `ai-review.yml` / `ai-triage.yml` — explicit permissions added (0c173ce)

### Release Version Convention

Version format: `vMAJOR.MINOR.PATCH` (e.g., `v0.0.26`, standard SemVer without fork suffix)

Python/PyPI equivalent: `MAJOR.MINOR.PATCH.postN` (e.g., `0.0.23.post2`)

When creating a new release tag manually: `git tag v0.0.23-fork.3 && git push origin v0.0.23-fork.3`

## Development Standards

### Required Before Each Commit

- Run linting to ensure Markdown files follow standards:

  ```bash
  npx markdownlint-cli2 "**/*.md"
  ```

- Ensure all changes follow the project's coding conventions
- Update `CHANGELOG.md` for any changes to the Specify CLI (when modifying `src/specify_cli/__init__.py`)
- Increment version in `pyproject.toml` for CLI changes

### Development Flow

- **Setup**: `uv sync` (install dependencies)
- **Run CLI**: `uv run specify --help`
- **Test locally**: `uv run specify init test-project --ai <agent-name>`
- **Create release packages**: `./.github/workflows/scripts/create-release-packages.sh v1.0.0`
- **Lint Markdown**: `npx markdownlint-cli2 "**/*.md"`

### Testing Changes Locally

When testing template or command changes:

1. Generate local release packages:

   ```bash
   ./.github/workflows/scripts/create-release-packages.sh v1.0.0
   ```

1. Copy the relevant package to your test project:

   ```bash
   cp -r .genreleases/sdd-copilot-package-sh/. <path-to-test-project>/
   ```

1. Test the agent in your test project directory

## Repository Structure

```text
.github/                 # GitHub configuration, workflows, and Copilot agent files
├── workflows/          # CI/CD workflows (lint, release, docs)
│   └── scripts/        # Release and package creation scripts
├── CODEOWNERS          # Code ownership definitions
└── copilot-instructions.md  # This file

.devcontainer/          # Development container configuration
memory/                 # Project constitution and principles
├── constitution.md     # Template for project constitutions

scripts/                # Development and automation scripts
├── bash/              # Bash scripts for Linux/macOS
│   ├── check-prerequisites.sh      # Verify installed tools
│   ├── common.sh                   # Shared utility functions
│   ├── create-new-feature.sh       # Create new feature branches
│   ├── setup-plan.sh               # Initialize implementation plans
│   └── update-agent-context.sh     # Update AI agent context files
└── powershell/        # PowerShell scripts for Windows/cross-platform
    ├── check-prerequisites.ps1
    ├── common.ps1
    ├── create-new-feature.ps1
    ├── setup-plan.ps1
    └── update-agent-context.ps1

src/specify_cli/            # Python source code for Specify CLI
    └── __init__.py         # Main CLI implementation (AGENT_CONFIG lives here)

templates/              # Templates for SDD workflow
├── agent-file-template.md     # Template for agent context files
├── checklist-template.md      # Feature checklist template
├── plan-template.md           # Implementation plan template
├── spec-template.md           # Feature specification template
├── tasks-template.md          # Task breakdown template
├── vscode-settings.json       # VS Code configuration
└── commands/                  # Slash command templates for AI agents
    ├── analyze.md
    ├── checklist.md
    ├── clarify.md
    ├── constitution.md
    ├── implement.md
    ├── plan.md
    ├── specify.md
    ├── tasks.md
    └── taskstoissues.md

docs/                   # Documentation
media/                  # Images, logos, and media assets

```

## Key Guidelines

### 1. Minimal Changes Philosophy

- Make the **smallest possible changes** to address issues
- Preserve existing functionality unless explicitly required to change
- Follow the existing code patterns and conventions
- Don't refactor unrelated code

### 2. Agent Configuration (AGENT_CONFIG)

The `AGENT_CONFIG` dictionary in `src/specify_cli/__init__.py` is the **single source of truth** for all AI agent metadata. When adding new agent support:

- **CRITICAL**: Use the **actual CLI tool name** as the dictionary key (e.g., `"cursor-agent"` not `"cursor"`)
- This eliminates special-case mappings throughout the codebase
- Each agent has: `name`, `folder`, `install_url`, `requires_cli`
- See `AGENTS.md` for the complete step-by-step guide for adding new agents

### 3. Version Management

Changes to `src/specify_cli/__init__.py` require:

- Version increment in `pyproject.toml`
- Entry in `CHANGELOG.md` describing the changes
- Testing with `uv run specify` to ensure CLI works

### 4. Documentation Standards

- Keep documentation up-to-date with code changes
- Follow Markdown linting rules (`.markdownlint-cli2.jsonc`)
- Update `README.md` for user-facing changes
- Update `AGENTS.md` when adding new agent support
- Update `spec-driven.md` for methodology changes

### 5. AI Agent Support

The toolkit supports 15+ AI coding assistants. Each agent has:

- Specific directory structure (`.claude/`, `.github/agents/`, `.windsurf/workflows/`, etc.)
- Command file format (Markdown or TOML)
- Argument patterns (`$ARGUMENTS` for Markdown, `{{args}}` for TOML)

When working with agents:

- Consult `AGENTS.md` for detailed integration guidelines
- Test agent commands after template changes
- Ensure script variants work (bash and PowerShell)

### 6. Spec-Driven Development (SDD) Workflow

The core SDD workflow consists of:

1. **Constitution** (`/speckit.constitution`): Establish project principles
2. **Specification** (`/speckit.specify`): Define what to build (the "what" and "why")
3. **Planning** (`/speckit.plan`): Create technical implementation plan (the "how")
4. **Tasks** (`/speckit.tasks`): Break down into actionable items
5. **Implementation** (`/speckit.implement`): Execute the plan

### 7. Code Quality Standards

- Python 3.11+ required
- Use `uv` for package management
- Follow PEP 8 style guidelines
- Write clear, self-documenting code
- Add docstrings for functions and classes
- Handle errors gracefully with informative messages

### 8. Testing and Validation

- Test CLI commands thoroughly before committing
- Verify templates work with multiple AI agents
- Test both bash and PowerShell script variants
- Ensure backward compatibility with existing projects
- Test in development container when possible

### 9. Contribution Disclosure

If using **any kind of AI assistance** (agents, ChatGPT, etc.) while contributing:

- **Must be disclosed** in the pull request or issue
- Include the extent of AI assistance (documentation comments vs. code generation)
- Disclose if PR responses/comments are AI-generated

### 10. Pull Request Guidelines

Large changes that materially impact the CLI or repository must be:

- **Discussed and agreed upon** by project maintainers beforehand
- PRs without prior conversation/agreement will be closed

Keep PRs focused:

- One logical change per PR
- Update relevant documentation
- Write good commit messages
- Test with the SDD workflow

### 11. Issue Management (Phased Execution)

- **Taxonomy:** All engineering tasks must be prefixed with `[PhX]` (e.g., `[Ph0] [BUG] ...`).
- **Phases:**
  - `Ph0`: Blockers (Serial)
  - `Ph1`: Core Enablers (Serial)
  - `Ph2`: Automation (Parallel)
  - `Ph3`: Integration (Parallel)
  - `Ph4`: Quality (Parallel)
  - `Ph5`: UX (Parallel)
  - `Ph6`: Backlog (Parallel)
- **Protocol:** Respect dependencies; do not implement `Ph3` before `Ph2` is ready.

## Common Commands Reference

```bash
# Install Specify CLI from this fork (with Phase 0 integration)
uv tool install specify-cli --from git+https://github.com/nsalvacao/spec-kit.git

# Note: The upstream repository is github/spec-kit. This fork includes Phase 0: AI System Ideation.

# Initialize new project
specify init <project-name> --ai <agent-name>

# Initialize in current directory
specify init . --ai claude
specify init --here --ai copilot

# Check installed tools
specify check

# Development setup
uv sync                    # Install dependencies
uv run specify --help      # Test CLI
```

## Supported AI Agents

- Copilot
- Claude Code
- Gemini CLI
- Cursor
- Qwen Code
- opencode
- Codex CLI
- Windsurf
- Kilo Code
- Auggie CLI
- Roo Code
- CodeBuddy CLI
- Qoder CLI
- Amazon Q Developer CLI
- Amp
- SHAI
- IBM Bob

See `README.md` for the full list with links and support status.

## Important Files to Know

- `AGENTS.md`: Comprehensive guide for adding new AI agent support
- `CONTRIBUTING.md`: Contribution guidelines and development workflow
- `spec-driven.md`: Detailed explanation of the SDD methodology
- `README.md`: User-facing documentation and getting started guide
- `pyproject.toml`: Python project configuration and version
- `CHANGELOG.md`: Version history and changes

## Phase 0: AI System Ideation

This fork includes **Phase 0: AI System Ideation** integrated before the standard SDD workflow. This phase focuses on exploring the problem space and generating ideas before diving into formal specifications.
