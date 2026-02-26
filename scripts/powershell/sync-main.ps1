#!/usr/bin/env pwsh
[CmdletBinding()]
param(
    [switch]$Apply,
    [string]$Remote = "origin",
    [switch]$Help
)

$ErrorActionPreference = "Stop"

if ($Help) {
    Write-Output @"
Usage: sync-main.ps1 [-Apply] [-Remote <name>] [-Help]

Synchronize local main with remote main and optionally prune stale local branches.

Options:
  -Apply          Delete local branches whose upstream is [gone]
  -Remote <name>  Remote name to sync from (default: origin)
  -Help           Show this help message
"@
    exit 0
}

function Invoke-GitChecked {
    param(
        [Parameter(Mandatory = $true)]
        [string[]]$Arguments,
        [Parameter(Mandatory = $true)]
        [string]$ErrorMessage
    )

    & git @Arguments
    if ($LASTEXITCODE -ne 0) {
        Write-Output "ERROR: $ErrorMessage"
        exit 1
    }
}

function Test-GitRefExists {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Ref
    )

    & git show-ref --verify --quiet $Ref 2>$null
    return ($LASTEXITCODE -eq 0)
}

git rev-parse --show-toplevel 2>$null | Out-Null
if ($LASTEXITCODE -ne 0) {
    Write-Output "ERROR: Not inside a git repository."
    exit 1
}

git remote get-url $Remote 2>$null | Out-Null
if ($LASTEXITCODE -ne 0) {
    Write-Output "ERROR: Remote '$Remote' not found."
    exit 1
}

Write-Output "Fetching '$Remote' with prune..."
Invoke-GitChecked -Arguments @("fetch", $Remote, "--prune") -ErrorMessage "Failed to fetch remote '$Remote'."

$hasLocalMain = Test-GitRefExists -Ref "refs/heads/main"

if ($hasLocalMain) {
    Write-Output "Checking out 'main'..."
    Invoke-GitChecked -Arguments @("checkout", "main") -ErrorMessage "Failed to checkout local 'main' branch."
} else {
    $hasRemoteMain = Test-GitRefExists -Ref "refs/remotes/$Remote/main"
    if ($hasRemoteMain) {
        Write-Output "Creating local 'main' from '$Remote/main'..."
        Invoke-GitChecked -Arguments @("checkout", "-b", "main", "$Remote/main") -ErrorMessage "Failed to create local 'main' from '$Remote/main'."
    } else {
        Write-Output "ERROR: Branch 'main' not found locally or at '$Remote/main'."
        exit 1
    }
}

Write-Output "Fast-forward pulling '$Remote/main'..."
Invoke-GitChecked -Arguments @("pull", "--ff-only", $Remote, "main") -ErrorMessage "Failed to fast-forward 'main' from '$Remote/main'."

$goneBranches = @()
$refs = git for-each-ref --format='%(refname:short)|%(upstream:track)' refs/heads
foreach ($line in $refs) {
    if (-not $line) { continue }
    $parts = $line -split '\|', 2
    $branch = $parts[0].Trim()
    $track = if ($parts.Count -gt 1) { $parts[1] } else { "" }
    if ($branch -and $branch -ne "main" -and $track -match 'gone') {
        $goneBranches += $branch
    }
}

if ($goneBranches.Count -eq 0) {
    Write-Output "No stale local branches with [gone] upstream."
    exit 0
}

Write-Output "Stale local branches ([gone] upstream):"
foreach ($branch in $goneBranches) {
    Write-Output "  - $branch"
}

if (-not $Apply) {
    Write-Output ""
    Write-Output "Dry-run mode (default): no branches deleted."
    Write-Output "Re-run with -Apply to delete the stale branches listed above."
    exit 0
}

Write-Output ""
Write-Output "Deleting stale local branches..."
foreach ($branch in $goneBranches) {
    try {
        git branch -d $branch | Out-Null
        if ($LASTEXITCODE -eq 0) {
            Write-Output "  ✓ deleted $branch"
        } else {
            Write-Output "  ✗ skipped $branch (not fully merged or deletion blocked)"
        }
    } catch {
        Write-Output "  ✗ skipped $branch (not fully merged or deletion blocked)"
    }
}
