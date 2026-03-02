<div align="center">
  <img src="./media/logo_large.webp" alt="Nexo Spec Kit logo" width="200" height="200" />
  <h1>Nexo Spec Kit</h1>
  <p><strong>The structured AI development toolkit that turns ideas into executable specifications.</strong></p>
  <p>Phase 0 AI ideation · Enterprise governance · 18 AI coding agents · Upstream-compatible.</p>
</div>

<p align="center">
  <a href="https://github.com/nsalvacao/spec-kit/actions/workflows/test.yml"><img src="https://github.com/nsalvacao/spec-kit/actions/workflows/test.yml/badge.svg" alt="Tests"></a>
  <a href="https://github.com/nsalvacao/spec-kit/actions/workflows/lint.yml"><img src="https://github.com/nsalvacao/spec-kit/actions/workflows/lint.yml/badge.svg" alt="Lint"></a>
  <a href="https://github.com/nsalvacao/spec-kit/actions/workflows/release.yml"><img src="https://github.com/nsalvacao/spec-kit/actions/workflows/release.yml/badge.svg" alt="Release"></a>
  <a href="https://github.com/nsalvacao/spec-kit/actions/workflows/docs.yml"><img src="https://github.com/nsalvacao/spec-kit/actions/workflows/docs.yml/badge.svg" alt="Docs"></a>
  <a href="https://github.com/nsalvacao/spec-kit/blob/main/LICENSE"><img src="https://img.shields.io/github/license/nsalvacao/spec-kit" alt="License"></a>
  <a href="https://nsalvacao.github.io/spec-kit/"><img src="https://img.shields.io/badge/docs-GitHub%20Pages-blue" alt="Documentation"></a>
</p>

---

## Table of Contents

- [What This Project Is](#what-this-project-is)
- [Why This Project Exists](#why-this-project-exists)
- [Core Capabilities](#core-capabilities)
- [Workflow at a Glance](#workflow-at-a-glance)
- [Supported AI Agents](#supported-ai-agents)
- [What is `uv`?](#what-is-uv)
- [Install](#install)
- [Quick Start](#quick-start)
- [CLI Reference](#cli-reference)
- [Extension System](#extension-system)
- [Repository Structure](#repository-structure)
- [Compatibility and Upstream Sync](#compatibility-and-upstream-sync)
- [Documentation Index](#documentation-index)
- [Development and Testing](#development-and-testing)
- [Security, Support, and Governance](#security-support-and-governance)
  - [Legal and Compliance](#legal-and-compliance)
- [Roadmap](#roadmap)
- [License](#license)

## What This Project Is

**Nexo Spec Kit** is a structured AI development toolkit and CLI for teams who
build software with AI agents. It implements a complete Spec-Driven Development
(SDD) pipeline that starts *before* any code is written:

- **Phase 0 — Ideate**: Structured AI ideation (IDEATE → SELECT → STRUCTURE →
  VALIDATE) to discover *what* to build before writing a single spec.
- **Phase 1 — Specify**: Author executable specifications that constrain AI
  agents to the right scope.
- **Phase 2 — Plan and implement**: Generate traceable implementation plans and
  delegate execution to AI agents.
- **Phase 3 — Validate**: Automated scope gates, contract validation, and
  handoff metadata create an auditable trail from idea to shipped code.

Nexo Spec Kit maintains **optional upstream compatibility** with
`github/spec-kit`. Set `SPECIFY_TEMPLATE_REPO=github/spec-kit` or use
`--template-repo github/spec-kit` to use upstream templates. This toolkit is
**not affiliated with GitHub**. See `docs/trademarks.md`.

For the full product identity and strategic positioning, see
[`docs/positioning.md`](docs/positioning.md).

## Why This Project Exists

AI coding agents are excellent at *implementing* but poor at *deciding what to
build*. Without a structured front-end discovery phase, teams accumulate
poorly-scoped features, duplicated agent context, and brittle handoffs.

Nexo Spec Kit closes this gap by adding a complete Phase 0 ideation layer on
top of the Spec-Driven Development workflow, plus enterprise-grade governance
that makes every AI decision traceable and auditable:

- Phase 0 AI ideation workflow (`ideate → select → structure → validate`)
- 18 AI coding agent integrations (the same named agents as upstream)
- 5 additional CLI commands vs upstream (`hierarchy-contract`, `scope-detect`, `scope-gate`, `productivity`, `update`)
- contract validation, scope gates, and handoff metadata
- enterprise compliance checker and operational release/deploy workflows

## Core Capabilities

- `specify init` project bootstrap with:
  - single or multi-agent selection (`--ai claude` or `--ai copilot,claude`)
  - script type control (`--script sh|ps`)
  - dry-run and automation flags (`--dry-run`, `--no-banner`, `--no-git`)
  - template source override (`--template-repo`, `SPECIFY_TEMPLATE_REPO`)
- Phase 0 slash-command set:
  - `/speckit.brainstorm` (optional strategic pre-phase that feeds IDEATE)
  - `/speckit.ideate`
  - `/speckit.select`
  - `/speckit.structure`
  - `/speckit.validate`
- SDD slash-command set:
  - `/speckit.constitution`
  - `/speckit.specify`
  - `/speckit.clarify`
  - `/speckit.plan`
  - `/speckit.tasks`
  - `/speckit.implement`
  - `/speckit.amend`
  - `/speckit.analyze`
  - `/speckit.checklist`
  - `/speckit.taskstoissues`
- Runtime utility commands:
  - `specify check`
  - `specify version`
  - `specify update`
- Extension management:
  - `specify extension list|add|remove|search|info|update|enable|disable`

## Workflow at a Glance

### Phase 0 (recommended before SDD)

`IDEATE -> SELECT -> STRUCTURE -> VALIDATE`

Optional strategic pre-step:

`BRAINSTORM -> IDEATE -> SELECT -> STRUCTURE -> VALIDATE`

Purpose:

- explore alternatives early
- score and select a direction
- capture vision artifacts
- gate feasibility before implementation planning

### Spec-Driven Development

`CONSTITUTION -> SPECIFY -> CLARIFY -> PLAN -> TASKS -> IMPLEMENT`

Purpose:

- encode project principles
- define what to build before how to build
- generate implementation artifacts and actionable tasks

## Supported AI Agents

`specify init --ai <agent>` supports the following values:

| `--ai` value | Agent | Type | Output Folder |
| --- | --- | --- | --- |
| `copilot` | GitHub Copilot | IDE | `.github/` |
| `claude` | Claude Code | CLI | `.claude/` |
| `gemini` | Gemini CLI | CLI | `.gemini/` |
| `cursor-agent` | Cursor | IDE | `.cursor/` |
| `qwen` | Qwen Code | CLI | `.qwen/` |
| `opencode` | opencode | CLI | `.opencode/` |
| `codex` | Codex CLI | CLI | `.codex/` |
| `windsurf` | Windsurf | IDE | `.windsurf/` |
| `kilocode` | Kilo Code | IDE | `.kilocode/` |
| `auggie` | Auggie CLI | CLI | `.augment/` |
| `codebuddy` | CodeBuddy | CLI | `.codebuddy/` |
| `qoder` | Qoder CLI | CLI | `.qoder/` |
| `roo` | Roo Code | IDE | `.roo/` |
| `q` | Amazon Q Developer CLI | CLI | `.amazonq/` |
| `amp` | Amp | CLI | `.agents/` |
| `shai` | SHAI | CLI | `.shai/` |
| `agy` | [Antigravity](https://antigravity.google/) | IDE | `.agent/` |
| `bob` | IBM Bob | IDE | `.bob/` |

For per-agent details and install links, see `docs/agents.md` and the live `AGENT_CONFIG` in `src/specify_cli/__init__.py`.

## What is `uv`?

**[`uv`](https://docs.astral.sh/uv/)** is an extremely fast Python package and project manager, written in Rust. It's a modern replacement for tools like `pip`, `pip-tools`, `pipx`, `poetry`, `pyenv`, and `virtualenv` — all in a single, blazingly fast tool.

### Why Spec Kit Uses `uv`

Spec Kit uses `uv` because it:

- **Installs and manages Python versions** automatically
- **Installs Python packages 10-100x faster** than pip
- **Provides a built-in tool manager** (replacing `pipx`) for CLI tools like `specify`
- **Works consistently** across macOS, Linux, and Windows
- **Requires zero configuration** to get started

### Installing `uv`

#### macOS and Linux

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

#### Windows

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

#### Alternative Installation Methods

##### macOS (Homebrew)

```bash
brew install uv
```

##### Linux (snap)

```bash
sudo snap install astral-uv --classic
```

##### With pip

```bash
pip install uv
```

For more installation options and troubleshooting, see the [official uv installation guide](https://docs.astral.sh/uv/getting-started/installation/).

### Verifying Installation

After installation, verify that `uv` is available:

```bash
uv --version
```

## Install

### Prerequisites

- Python `3.11+`
- `uv` (recommended package/runtime manager)
- Git
- AI agent of your choice from the table above
- `ripgrep` (`rg`) recommended for validator scripts
- `yq` recommended for broader script/tooling compatibility checks

### Option A: One-time execution (fastest)

```bash
uvx --from git+https://github.com/nsalvacao/spec-kit.git specify init my-project --ai codex
```

### Option B: Persistent CLI installation

```bash
uv tool install specify-cli --from git+https://github.com/nsalvacao/spec-kit.git
specify --help
```

### Option C: Alternative package managers

```bash
pipx install git+https://github.com/nsalvacao/spec-kit.git
# or
pip install git+https://github.com/nsalvacao/spec-kit.git
```

## Quick Start

### 1) Initialize a project

```bash
specify init my-project --ai codex
cd my-project
```

Use current directory mode if needed:

```bash
specify init . --ai claude --script sh
```

When `.specify/` already exists, init preserves it by default:

```bash
specify init . --ai gemini
```

Use `--force` only when you explicitly want to reinitialize and overwrite `.specify`:

```bash
specify init . --ai gemini --force
```

Initialize with Antigravity support:

```bash
specify init my-project --ai agy
```

### 2) Run Phase 0 in your agent chat

```text
/speckit.ideate
/speckit.select
/speckit.structure
/speckit.validate
```

### 3) Continue with SDD commands

```text
/speckit.constitution
/speckit.specify
/speckit.clarify
/speckit.plan
/speckit.tasks
/speckit.implement
```

### 4) Optional quality helpers

```text
/speckit.amend
/speckit.checklist
/speckit.analyze
/speckit.taskstoissues
```

### 5) Keep CLI updated

```bash
specify update
```

If `codex` is selected, `init` also prints a `CODEX_HOME` setup hint for project-scoped prompts.

## CLI Reference

### Top-level commands

| Command | Description |
| --- | --- |
| `specify init` | Initialize project from templates and generate agent command packs |
| `specify check` | Validate required/recommended tools and agent CLIs |
| `specify version` | Show CLI, template, and environment version info |
| `specify update` | Check for updates and optionally upgrade CLI |
| `specify extension ...` | Manage extensions in `.specify/extensions/` |

### High-value `init` options

| Option | Purpose |
| --- | --- |
| `--ai` | Select one or more agents (`a,b,c`) |
| `--script sh\|ps` | Force POSIX or PowerShell script variant |
| `--template-repo` | Override template source repo (`owner/name`) |
| `--here` / `.` | Initialize in current directory |
| `--force` | Skip prompts and overwrite existing `.specify` content when reinitializing |
| `--ignore-agent-tools` | Skip CLI tool checks for selected agents |
| `--dry-run` | Preview without writing files |
| `--no-banner` | Suppress ASCII banner (CI-friendly) |
| `--no-git` | Skip git init |
| `--github-token` | Use token for GitHub API operations |
| `--skip-tls` | Disable TLS verification (local troubleshooting only) |
| `--local-templates` | Path to local `.genreleases` dir for development testing (bypasses GitHub download) |

## Extension System

This fork includes an extension framework and CLI lifecycle commands.

```bash
specify extension list
specify extension search
specify extension add <name-or-path>
specify extension info <name>
specify extension remove <name>
```

Notes:

- extension commands must run from a spec-kit project root (`.specify/` present)
- local/dev and URL-based installation are supported
- catalog and extension templates live under `extensions/`

See:

- `extensions/EXTENSION-USER-GUIDE.md`
- `extensions/EXTENSION-DEVELOPMENT-GUIDE.md`
- `extensions/RFC-EXTENSION-SYSTEM.md`

## Repository Structure

```text
spec-kit/
├── src/specify_cli/              # CLI implementation
├── templates/                    # Slash-command and artifact templates
├── scripts/                      # Bash, PowerShell, and Python automation scripts
├── docs/                         # Markdown docs source
├── docs-site/                    # MkDocs site and published docs assets
├── extensions/                   # Extension framework, docs, and templates
├── tests/                        # Pytest suite
├── .github/workflows/            # CI/CD pipelines
├── spec-driven.md                # Methodology reference
└── AGENTS.md                     # Agent operating guidance for this repo
```

## Compatibility and Upstream Sync

- Default template source is this fork: `nsalvacao/spec-kit`
- You can opt into upstream templates:

```bash
export SPECIFY_TEMPLATE_REPO=github/spec-kit
specify init my-project --ai codex
```

Or per command:

```bash
specify init my-project --template-repo github/spec-kit --ai codex
```

Detailed policy:

- `docs/compatibility.md`
- `docs/upstream-sync.md`

## Documentation Index

| Topic | Link |
| --- | --- |
| **Product positioning** | `docs/positioning.md` |
| **ADR — Positioning model** | `docs/adr-positioning-model.md` |
| Getting started | `docs/quickstart.md` |
| Installation | `docs/installation.md` |
| Configuration | `docs/configuration.md` |
| Scope scoring rubric | `docs/scope-scoring-rubric.md` |
| Scope gate contract | `docs/scope-gate-consumption-contract.md` |
| CLI reference | `docs/cli.md` |
| Agent support | `docs/agents.md` |
| Methodology | `docs/methodology.md` |
| Walkthrough | `docs/walkthrough.md` |
| Upgrade guidance | `docs/upgrade.md` |
| Release process | `docs/release.md` |
| Distribution | `docs/distribution.md` |
| Compatibility | `docs/compatibility.md` |
| Upstream sync | `docs/upstream-sync.md` |
| GitHub Pages site | `https://nsalvacao.github.io/spec-kit/` |

## Development and Testing

### Local setup

```bash
uv sync
uv run specify --help
```

### Run tests

```bash
uv run pytest tests/ --tb=short -v
```

### Build docs locally

```bash
pip install mkdocs-material
mkdocs build -f docs-site/mkdocs.yml -d docs-site/site
```

More details:

- `CONTRIBUTING.md`
- `docs/local-development.md`

## Security, Support, and Governance

- Security policy: `SECURITY.md`
- Support process: `SUPPORT.md`
- Code of conduct: `CODE_OF_CONDUCT.md`
- Contribution rules and phase taxonomy: `CONTRIBUTING.md`

If you use AI assistance in contributions, disclosure is required (see `CONTRIBUTING.md`).

### Legal and Compliance

This fork is an independent derivative of `github/spec-kit` distributed under the MIT license.
Trademark usage is attribution-only; this fork is **not affiliated with GitHub**.

- License and copyright obligations: [`docs/legal-compliance.md`](docs/legal-compliance.md)
- Upstream intake provenance workflow: [`docs/provenance-playbook.md`](docs/provenance-playbook.md)
- Trademark-safe usage guidance: [`docs/trademarks.md`](docs/trademarks.md)
- Upstream synchronization policy: [`docs/upstream-sync.md`](docs/upstream-sync.md)

Compliance is enforced automatically via the `compliance-guard` CI workflow on every
push and pull request.

## Roadmap

Roadmap and evolution priorities:

- `ROADMAP.md`
- open issues: `https://github.com/nsalvacao/spec-kit/issues`

## License

MIT. See `LICENSE`.
