---
applyTo: "scripts/powershell/*.ps1"
---

# PowerShell Script Development Instructions

When working on PowerShell scripts in `scripts/powershell/`, follow these guidelines:

## Script Standards

1. **Functions**: Use approved PowerShell verbs (Get-, Set-, New-, etc.)
2. **Parameters**: Define typed parameters with `[Parameter()]` attributes
3. **Error Handling**: Use `try/catch` blocks and `$ErrorActionPreference`
4. **Variables**: Use PascalCase for variables and functions
5. **Comments**: Use `#` for single-line, `<# #>` for multi-line comments

## Common Patterns

- **Source common.ps1**: Most scripts source `scripts/powershell/common.ps1` for shared utilities
- **Color Output**: Use `Write-Host -ForegroundColor` for colored output
- **Error Messages**: Use `Write-Error` for errors
- **Path Handling**: Use `Join-Path` and `Resolve-Path` for cross-platform paths
- **Tool Checks**: Use `Get-Command` to check if tools are installed

## Testing Requirements

Test scripts on both Windows and cross-platform:

```powershell
# Test execution
.\scripts\powershell\new-script.ps1

# Test with different scenarios
.\scripts\powershell\new-script.ps1 -Help
.\scripts\powershell\new-script.ps1 -Parameter Value
```

## Cross-Platform Considerations

- PowerShell Core (7+) runs on Linux, macOS, and Windows
- Avoid Windows-specific cmdlets unless necessary
- Use `$PSScriptRoot` for script location
- Handle path separators correctly (`/` vs `\`)
- Test on Windows PowerShell 5.1 AND PowerShell Core 7+

## Bash Equivalent

**IMPORTANT**: When adding or modifying PowerShell scripts, ensure there's an equivalent Bash script in `scripts/bash/` with the same functionality. Both script variants must be kept in sync.

See `scripts/bash/common.sh` for Bash patterns.

## Style Guidelines

- Use 4-space indentation (not tabs)
- Place opening braces on the same line
- Use explicit parameter types
- Avoid aliases in scripts (use full cmdlet names)
- Add help comments with `.SYNOPSIS`, `.DESCRIPTION`, `.PARAMETER`
