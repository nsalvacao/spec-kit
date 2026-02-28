# Dogfooding Report

This document records end-to-end dogfooding of the Specify CLI, executed against the
spec-kit repository itself. The goal is to prove that every user-facing command works
in a real environment and that `specify init` produces a valid project scaffold.

## Environment

| Property | Value |
| --- | --- |
| CLI Version | 0.0.73 |
| Python | 3.12 |
| Platform | Linux x86_64 |
| Package Manager | uv |

## 1 — `specify --help`

**Command:** `uv run specify --help`

**Result:** ✅ Success (exit code 0)

The CLI printed the banner and listed all available sub-commands:

- `init` — Initialize a new Specify project from the latest template.
- `check` — Check that all required tools are installed.
- `version` — Display version and system information.
- `hierarchy-contract` — Normalize and validate hierarchy contract payload.
- `scope-detect` — Run scope detection and emit gate-ready structured output.
- `scope-gate` — Run mandatory decomposition gate with override/risk controls.
- `update` — Check for updates and optionally upgrade specify CLI.
- `extension` — Manage spec-kit extensions.

## 2 — `specify check`

**Command:** `uv run specify check`

**Result:** ✅ Success (exit code 0)

Tool availability summary:

| Tool | Status |
| --- | --- |
| Git | ✅ Available |
| Python 3 | ✅ Available |
| uv | ✅ Available |
| yq | ✅ Available |
| ripgrep (rg) | ⚠ Not found (optional) |
| AI assistants | ○ IDE-based (no CLI check) or not installed |

The CLI printed "Specify CLI is ready to use!" confirming the core toolchain is
functional.

## 3 — `specify init` (end-to-end scaffold)

**Command:** `uv run specify init /tmp/dogfood-test --ai copilot`

**Result:** ✅ Success (exit code 0)

### Initialization steps observed

| Step | Outcome |
| --- | --- |
| Check required tools | ○ rg not found (non-blocking warning) |
| Select AI assistant | ✅ copilot |
| Select script type | ✅ sh (default) |
| Fetch latest release | ✅ v0.0.73 (125,534 bytes) |
| Download template | ✅ spec-kit-template-copilot-sh-v0.0.73.zip |
| Extract template | ✅ 82 entries |
| Ensure scripts executable | ✅ 33 updated |
| Configure .gitignore | ✅ Security patterns added |
| Constitution setup | ✅ Copied from template |
| Project config setup | ✅ Copied from template |
| Initialize git repository | ⚠ Commit failed (no git identity configured — expected in CI) |
| Finalize | ✅ Project ready |

### Generated project structure

```text
/tmp/dogfood-test/
├── .github/
│   ├── agents/          (14 agent files — speckit.*.agent.md)
│   └── prompts/         (14 prompt files — speckit.*.prompt.md)
├── .specify/
│   ├── memory/
│   ├── scripts/bash/
│   └── templates/       (10 template files)
├── .vscode/
│   └── settings.json
└── .gitignore
```

Total files generated: **82** (excluding `.git` internals).

### Slash commands available after init

Phase 0 commands: `ideate`, `select`, `structure`, `validate`

Core SDD commands: `constitution`, `specify`, `clarify`, `plan`, `tasks`, `implement`, `amend`

Quality helpers: `analyze`, `checklist`, `taskstoissues`

## 4 — Test suite

**Command:** `uv run pytest tests/ --tb=short`

**Result:** 522 passed, 40 failed (all 40 failures caused by missing `rg` binary — unrelated to CLI logic), 9 skipped.

## Reproducing this report

Run the following commands from the repository root:

```bash
uv sync
uv run specify --help
uv run specify check
uv run specify init /tmp/dogfood-test --ai copilot
uv run pytest tests/ --tb=short
```
