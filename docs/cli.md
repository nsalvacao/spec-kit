# Specify CLI Reference (Fork)

This reference covers the `specify` CLI and the available slash commands after initialization.

## CLI Commands

| Command | Description |
| --- | --- |
| `init` | Initialize a new Specify project from templates |
| `check` | Check for installed tools and agent CLIs |

## `specify init` Arguments & Options

| Argument/Option | Type | Description |
| --- | --- | --- |
| `<project-name>` | Argument | Name for the new project directory (optional if using `--here`, or use `.` for current directory) |
| `--ai` | Option | AI assistant to use: `claude`, `gemini`, `copilot`, `cursor-agent`, `qwen`, `opencode`, `codex`, `windsurf`, `kilocode`, `auggie`, `roo`, `codebuddy`, `amp`, `shai`, `q`, `bob`, or `qoder` |
| `--script` | Option | Script variant: `sh` (bash/zsh) or `ps` (PowerShell) |
| `--template-repo` | Option | Override template repo (owner/name). Defaults to `SPECIFY_TEMPLATE_REPO` or `nsalvacao/spec-kit` |
| `--ignore-agent-tools` | Flag | Skip checks for AI agent tools |
| `--no-git` | Flag | Skip git repository initialization |
| `--here` | Flag | Initialize project in current directory instead of creating a new one |
| `--force` | Flag | Force merge/overwrite when initializing in current directory |
| `--skip-tls` | Flag | Skip SSL/TLS verification (not recommended) |
| `--debug` | Flag | Enable debug output for troubleshooting |
| `--github-token` | Option | GitHub token for API requests (or set GH_TOKEN/GITHUB_TOKEN env variable) |

## Examples

```bash
specify init my-project --ai codex
specify init . --here --ai claude
specify init my-project --ai copilot --script ps
specify init my-project --ai gemini --no-git
specify check

```text

## Template Override (Fork Templates)

To use fork templates explicitly:

```bash
export SPECIFY_TEMPLATE_REPO=nsalvacao/spec-kit
specify init my-project --ai codex

# or per-command
specify init my-project --template-repo nsalvacao/spec-kit --ai codex
```

## Slash Commands (after init)

### Phase 0 (Recommended Prerequisite)

- `/speckit.ideate` - generate ideas backlog (SCAMPER + HMW)
- `/speckit.select` - AI-RICE scoring and selection
- `/speckit.structure` - AI vision canvas + vision brief
- `/speckit.validate` - Gate G0 validation

### Core SDD Workflow

- `/speckit.constitution`
- `/speckit.specify`
- `/speckit.plan`
- `/speckit.tasks`
- `/speckit.implement`

### Optional Commands

- `/speckit.clarify`
- `/speckit.analyze`
- `/speckit.checklist`

## Environment Variables

| Variable | Description |
| --- | --- |
| `SPECIFY_TEMPLATE_REPO` | Override template source repo (owner/name) |
| `SPECIFY_FEATURE` | Override feature detection when not using git branches |
