# Spec Kit - Copilot Instructions

This repository is an independent fork of `github/spec-kit` with **Phase 0: AI System Ideation** integrated before the standard Spec-Driven Development (SDD) workflow.

**Spec Kit** is a comprehensive toolkit for implementing Spec-Driven Development - a methodology that emphasizes creating clear specifications before implementation. The toolkit includes templates, scripts, and workflows that guide development teams through a structured approach to building software.

**Specify CLI** is the command-line interface that bootstraps projects with the Spec Kit framework, setting up necessary directory structures, templates, and AI agent integrations.

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

```text

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
