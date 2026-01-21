---
applyTo: "src/specify_cli/__init__.py"
---

# Python CLI Development Instructions

When working on the Specify CLI (`src/specify_cli/__init__.py`), follow these guidelines:

## Critical Requirements

1. **Version Management** - ANY change to `__init__.py` requires:
   - Increment version in `pyproject.toml` (follow semantic versioning)
   - Add entry to `CHANGELOG.md` describing the change
   - Test with `uv run specify --help` before committing

2. **AGENT_CONFIG is Sacred** - The `AGENT_CONFIG` dictionary is the **single source of truth**:
   - Use actual CLI tool names as keys (e.g., `"cursor-agent"` not `"cursor"`)
   - Never add special-case mappings for agent names
   - Maintain all four fields: `name`, `folder`, `install_url`, `requires_cli`
   - See `AGENTS.md` for the complete integration guide

## Code Standards

- **Python Version**: 3.11+ required
- **Style**: Follow PEP 8
- **Type Hints**: Use type hints for function parameters and return values
- **Error Handling**: Provide clear, actionable error messages with Rich formatting
- **Console Output**: Use Rich console for all user-facing output
- **Path Handling**: Always use `Path` from `pathlib` for file operations

## Testing Requirements

Before committing changes:

```bash
# Test CLI functionality
uv run specify --help
uv run specify check
uv run specify init test-project --ai copilot

# Test with actual templates
./.github/workflows/scripts/create-release-packages.sh v1.0.0
cp -r .genreleases/sdd-copilot-package-sh/. /tmp/test-project/
```

## Adding New Agent Support

Follow the step-by-step guide in `AGENTS.md`. Key steps:

1. Add to `AGENT_CONFIG` with actual CLI tool name as key
2. Update `--ai` parameter help text
3. Update README.md supported agents section
4. Update release scripts
5. Test thoroughly with `specify init`

## Common Patterns

- **Tool Checking**: Use `check_tool()` or `check_tool_for_tracker()` functions
- **User Input**: Use `Prompt.ask()` from Rich for interactive prompts
- **File Operations**: Always check if files exist before reading/writing
- **URL Handling**: Use `httpx` for HTTP requests with proper error handling
- **Cross-platform**: Ensure code works on Linux, macOS, and Windows
