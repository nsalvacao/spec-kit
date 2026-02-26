#!/usr/bin/env pwsh
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidateSet("patch", "minor", "major")]
    [string]$Part,
    [switch]$DryRun,
    [switch]$IncludeDiff,
    [string]$ReleaseDate,
    [string]$RepoRoot = ".",
    [string]$Map = ".github/version-map.yml",
    [switch]$Json,
    [switch]$Help
)

$ErrorActionPreference = "Stop"

if ($Help) {
    Write-Output @"
Usage: version-bump.ps1 -Part <patch|minor|major> [options]

Manifest-driven version bump for Spec Kit.

Options:
  -Part <value>       Required. One of: patch, minor, major
  -DryRun             Preview changes without writing files
  -IncludeDiff        Include unified diff preview in output
  -ReleaseDate <date> Optional changelog date (YYYY-MM-DD)
  -RepoRoot <path>    Repository root (default: .)
  -Map <path>         Version map manifest path (default: .github/version-map.yml)
  -Json               Emit compact JSON output
  -Help               Show this help message
"@
    exit 0
}

$command = @(
    "scripts/python/version-orchestrator.py",
    "bump",
    "--repo-root", $RepoRoot,
    "--map", $Map,
    "--part", $Part
)

if ($ReleaseDate) {
    $command += @("--release-date", $ReleaseDate)
}
if ($DryRun) {
    $command += "--dry-run"
}
if ($IncludeDiff) {
    $command += "--include-diff"
}
if ($Json) {
    $command += "--json"
}

& python $command
exit $LASTEXITCODE
