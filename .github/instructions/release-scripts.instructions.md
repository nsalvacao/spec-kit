---
applyTo: ".github/workflows/scripts/*.sh"
---

# Release and Workflow Script Instructions

When working on release and workflow scripts in `.github/workflows/scripts/`, follow these strict guidelines:

## Critical Requirements

1. **Testing is Mandatory**: These scripts create releases and packages. Test thoroughly before committing:

   ```bash
   # Test release package creation
   ./.github/workflows/scripts/create-release-packages.sh v1.0.0-test
   
   # Verify packages were created
   ls -la .genreleases/
   
   # Test a specific package
   cp -r .genreleases/sdd-copilot-package-sh/. /tmp/test-project/
   ```

2. **Agent Synchronization**: When adding a new agent, update ALL relevant scripts:
   - `create-release-packages.sh` - Add to `ALL_AGENTS` array and case statement
   - `create-github-release.sh` - Add package zip files to release command
   - Agent-specific generation logic must be consistent

3. **Version Handling**: Scripts must handle version strings correctly:
   - Accept version with or without 'v' prefix
   - Generate consistent package names
   - Handle semantic versioning (major.minor.patch)

## Script Structure

- **Error Handling**: Use `set -e` to exit on errors
- **Validation**: Validate inputs before processing
- **Logging**: Print clear status messages for each major step
- **Cleanup**: Clean up `.genreleases/` directory before creating new packages
- **Atomic Operations**: Use temporary directories, then move to final location

## Package Generation

When generating packages:

1. **Template Substitution**: Replace placeholders correctly:
   - `{SCRIPT}` → Actual script path
   - `$ARGUMENTS` or `{{args}}` → Kept as-is for agent use
   - `__AGENT__` → Agent display name

2. **Directory Structure**: Maintain correct agent-specific directory patterns:
   - CLI agents: `.<agent-name>/commands/`
   - IDE agents: Follow IDE-specific patterns

3. **File Formats**: Respect agent-specific formats:
   - Markdown: For Claude, Cursor, Copilot, etc.
   - TOML: For Gemini, Qwen

## Testing Checklist

Before committing changes to these scripts:

- [ ] Run the script locally with a test version
- [ ] Verify all expected packages are created in `.genreleases/`
- [ ] Test at least one package in a real project
- [ ] Verify file permissions are correct (scripts should be executable)
- [ ] Check that package sizes are reasonable
- [ ] Ensure no sensitive data is included in packages

## Common Pitfalls

- Forgetting to update `ALL_AGENTS` array when adding agents
- Inconsistent directory naming across agents
- Missing case statements for new agents
- Incorrect template variable substitution
- Not testing the actual generated packages
