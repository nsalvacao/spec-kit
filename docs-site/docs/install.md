# Install

This fork ships with Phase 0 as a recommended prerequisite before the core SDD workflow.

## Persistent Installation (recommended)

```bash
uv tool install specify-cli --from git+https://github.com/nsalvacao/spec-kit.git
```

## One-Time Usage

```bash
uvx --from git+https://github.com/nsalvacao/spec-kit.git specify init <PROJECT_NAME>
```

## Template Override

```bash
SPECIFY_TEMPLATE_REPO=nsalvacao/spec-kit specify init <PROJECT_NAME>
```
