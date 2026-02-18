# Fork Distribution Guide

This document explains how to install and use the fork, including template overrides and user-type guidance.

## Install Options

### Persistent Installation (recommended)

```bash
uv tool install specify-cli --from git+<https://github.com/nsalvacao/spec-kit.git>
```bash

Upgrade:

```bash
uv tool install specify-cli --force --from git+<https://github.com/nsalvacao/spec-kit.git>
```bash

### One-Time Usage

```bash
uvx --from git+<https://github.com/nsalvacao/spec-kit.git> specify init <PROJECT_NAME>
```bash

### Alternative Package Managers

```bash

# pipx

pipx install git+<https://github.com/nsalvacao/spec-kit.git>

# pip (virtualenv recommended)

pip install git+<https://github.com/nsalvacao/spec-kit.git>
```bash

## Template Override (Advanced)

By default, the forked CLI uses fork templates. You can override the template source explicitly if needed:

```bash
export SPECIFY_TEMPLATE_REPO=nsalvacao/spec-kit
specify init <PROJECT_NAME>
```bash

Or per command:

```bash
specify init <PROJECT_NAME> --template-repo nsalvacao/spec-kit

### Upstream Compatibility (Optional)

If you need upstream templates for compatibility testing:

```bash
export SPECIFY_TEMPLATE_REPO=github/spec-kit
specify init <PROJECT_NAME>

```bash
```bash

## Deployment / Usage by User Type

### CLI Users (local dev)

- Use `uv tool install` for a persistent CLI
- Fork templates are used by default; set `SPECIFY_TEMPLATE_REPO=github/spec-kit` only to opt-in to upstream templates

### IDE Users (Copilot / Claude / Cursor / Codex)

- Run `specify init` with `--ai` to generate agent commands
- Keep `CODEX_HOME` pointing at project prompts if using Codex CLI

### CI/CD or Automation

- Install via `uvx` or `pipx`
- Set `SPECIFY_TEMPLATE_REPO` in CI environment for reproducible templates
- Run `specify init` in a clean workspace

### Offline / Air-Gapped Environments

- Pre-download templates into your repo (`.specify/` or `templates/`)
- Use the `--template-repo` override only when you can reach GitHub
