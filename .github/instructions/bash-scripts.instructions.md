---
applyTo: "scripts/bash/*.sh"
---

# Bash Script Development Instructions

When working on Bash scripts in `scripts/bash/`, follow these guidelines:

## Script Standards

1. **Shebang**: Always use `#!/usr/bin/env bash` (not `/bin/sh`)
2. **Error Handling**: Use `set -e` to exit on errors where appropriate
3. **Variables**: Use `${VARIABLE}` syntax for clarity
4. **Functions**: Define functions before use, use descriptive names
5. **Comments**: Add comments for non-obvious logic

## Common Patterns

- **Source common.sh**: Most scripts source `scripts/bash/common.sh` for shared utilities
- **Color Output**: Use color codes defined in `common.sh` for user feedback
- **Error Messages**: Write to stderr for errors: `echo "Error" >&2`
- **Path Handling**: Use `REPO_ROOT` variable for repository root path
- **Tool Checks**: Use `command -v` to check if tools are installed

## Testing Requirements

Test scripts on both Linux and macOS:

```bash
# Make script executable
chmod +x scripts/bash/new-script.sh

# Test execution
./scripts/bash/new-script.sh

# Test with different scenarios
./scripts/bash/new-script.sh --help
./scripts/bash/new-script.sh <test-args>
```

## Cross-Platform Considerations

- Ensure compatibility with both GNU and BSD tools (Linux vs macOS)
- Avoid GNU-specific flags that don't exist in BSD variants
- Test path handling with spaces and special characters
- Use portable commands when possible

## PowerShell Equivalent

**IMPORTANT**: When adding or modifying Bash scripts, ensure there's an equivalent PowerShell script in `scripts/powershell/` with the same functionality. Both script variants must be kept in sync.

See `scripts/powershell/common.ps1` for PowerShell patterns.
