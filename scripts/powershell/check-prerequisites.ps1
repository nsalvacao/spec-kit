#!/usr/bin/env pwsh

# Consolidated prerequisite checking script (PowerShell)
#
# This script provides unified prerequisite checking for Spec-Driven Development workflow.
# It replaces the functionality previously spread across multiple scripts.
#
# Usage: ./check-prerequisites.ps1 [OPTIONS]
#
# OPTIONS:
#   -Json               Output in JSON format
#   -RequireTasks       Require tasks.md to exist (for implementation phase)
#   -IncludeTasks       Include tasks.md in AVAILABLE_DOCS list
#   -PathsOnly          Only output path variables (no validation)
#   -Help, -h           Show help message

[CmdletBinding()]
param(
    [switch]$Json,
    [switch]$RequireTasks,
    [switch]$IncludeTasks,
    [switch]$PathsOnly,
    [switch]$Help
)

$ErrorActionPreference = 'Stop'

# Show help if requested
if ($Help) {
    Write-Output @"
Usage: check-prerequisites.ps1 [OPTIONS]

Consolidated prerequisite checking for Spec-Driven Development workflow.

OPTIONS:
  -Json               Output in JSON format
  -RequireTasks       Require tasks.md to exist (for implementation phase)
  -IncludeTasks       Include tasks.md in AVAILABLE_DOCS list
  -PathsOnly          Only output path variables (no prerequisite validation)
  -Help, -h           Show this help message

EXAMPLES:
  # Check task prerequisites (plan.md required)
  .\check-prerequisites.ps1 -Json
  
  # Check implementation prerequisites (plan.md + tasks.md required)
  .\check-prerequisites.ps1 -Json -RequireTasks -IncludeTasks
  
  # Get feature paths only (no validation)
  .\check-prerequisites.ps1 -PathsOnly

"@
    exit 0
}

# Dependency checks (core tools used by Spec-Kit workflows)
$depsMissing = $false
$missingTools = @()

function Write-Dep {
    param([string]$Message)
    if ($Json) {
        Write-Warning $Message
    } else {
        Write-Output $Message
    }
}

function Get-InstallHints {
    param([string]$Tool)

    if ($IsMacOS) {
        switch ($Tool) {
            'git' { return @('brew install git') }
            'python' { return @('brew install python') }
            'uv' { return @('brew install uv', 'pipx install uv', 'pip install uv') }
            'yq' { return @('brew install yq') }
            'rg' { return @('brew install ripgrep') }
        }
    } elseif ($IsLinux) {
        switch ($Tool) {
            'git' { return @('sudo apt install git') }
            'python' { return @('sudo apt install python3') }
            'uv' { return @('pipx install uv', 'pip install uv') }
            'yq' { return @('sudo apt install yq') }
            'rg' { return @('sudo apt install ripgrep') }
        }
    } else {
        switch ($Tool) {
            'git' { return @('winget install --id Git.Git') }
            'python' { return @('winget install --id Python.Python.3') }
            'uv' { return @('pipx install uv', 'pip install uv') }
            'yq' { return @('winget install --id MikeFarah.yq') }
            'rg' { return @('winget install --id BurntSushi.ripgrep.MSVC') }
        }
    }
    return @()
}

function Add-MissingTool {
    param(
        [string]$Name,
        [string[]]$Hints
    )
    $script:depsMissing = $true
    $script:missingTools += [PSCustomObject]@{
        Name = $Name
        Hints = $Hints
    }
}

Write-Dep "Checking system dependencies..."

if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    Add-MissingTool -Name 'git' -Hints (Get-InstallHints 'git')
}

$pythonCmd = Get-Command python3 -ErrorAction SilentlyContinue
if (-not $pythonCmd) { $pythonCmd = Get-Command python -ErrorAction SilentlyContinue }
if (-not $pythonCmd) {
    Add-MissingTool -Name 'python3 (or python)' -Hints (Get-InstallHints 'python')
} else {
    # Check if PyYAML is installed
    $pyYamlCheck = & $pythonCmd -c "import yaml" 2>&1
    if ($LASTEXITCODE -ne 0) {
        Add-MissingTool -Name 'PyYAML' -Hints @('pip install pyyaml')
    }
}

if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
    Add-MissingTool -Name 'uv' -Hints (Get-InstallHints 'uv')
}

# yq is now optional - state management uses Python/PyYAML
if (-not (Get-Command yq -ErrorAction SilentlyContinue)) {
    Write-Output "⚠ Optional tool not found: yq (YAML processor)"
    Write-Output "  Note: State management now uses Python/PyYAML instead"
    Write-Output "  yq is still useful for manual YAML queries"
    foreach ($hint in (Get-InstallHints 'yq')) {
        Write-Output "  $hint"
    }
    Write-Output ""
}

if (-not (Get-Command rg -ErrorAction SilentlyContinue)) {
    Add-MissingTool -Name 'rg (ripgrep)' -Hints (Get-InstallHints 'rg')
}

if ($missingTools.Count -gt 0) {
    Write-Dep ("Missing required tools: {0}" -f (($missingTools | ForEach-Object { $_.Name }) -join ', '))
    foreach ($tool in $missingTools) {
        Write-Dep ("Install {0}:" -f $tool.Name)
        foreach ($hint in $tool.Hints) {
            if ($hint) { Write-Dep ("  {0}" -f $hint) }
        }
    }
    Write-Dep ""
}

# Source common functions
. "$PSScriptRoot/common.ps1"

# Get feature paths and validate branch
$paths = Get-FeaturePathsEnv

if (-not (Test-FeatureBranch -Branch $paths.CURRENT_BRANCH -HasGit:$paths.HAS_GIT)) { 
    exit 1 
}

# If paths-only mode, output paths and exit (support combined -Json -PathsOnly)
if ($PathsOnly) {
    if ($Json) {
        [PSCustomObject]@{
            REPO_ROOT    = $paths.REPO_ROOT
            BRANCH       = $paths.CURRENT_BRANCH
            FEATURE_DIR  = $paths.FEATURE_DIR
            FEATURE_SPEC = $paths.FEATURE_SPEC
            IMPL_PLAN    = $paths.IMPL_PLAN
            TASKS        = $paths.TASKS
        } | ConvertTo-Json -Compress
    } else {
        Write-Output "REPO_ROOT: $($paths.REPO_ROOT)"
        Write-Output "BRANCH: $($paths.CURRENT_BRANCH)"
        Write-Output "FEATURE_DIR: $($paths.FEATURE_DIR)"
        Write-Output "FEATURE_SPEC: $($paths.FEATURE_SPEC)"
        Write-Output "IMPL_PLAN: $($paths.IMPL_PLAN)"
        Write-Output "TASKS: $($paths.TASKS)"
    }
    if ($depsMissing) { exit 1 }
    exit 0
}

# Validate required directories and files
if (-not (Test-Path $paths.FEATURE_DIR -PathType Container)) {
    Write-Output "ERROR: Feature directory not found: $($paths.FEATURE_DIR)"
    Write-Output "Run /speckit.specify first to create the feature structure."
    exit 1
}

if (-not (Test-Path $paths.IMPL_PLAN -PathType Leaf)) {
    Write-Output "ERROR: plan.md not found in $($paths.FEATURE_DIR)"
    Write-Output "Run /speckit.plan first to create the implementation plan."
    exit 1
}

# Check for tasks.md if required
if ($RequireTasks -and -not (Test-Path $paths.TASKS -PathType Leaf)) {
    Write-Output "ERROR: tasks.md not found in $($paths.FEATURE_DIR)"
    Write-Output "Run /speckit.tasks first to create the task list."
    exit 1
}

# Build list of available documents
$docs = @()

# Always check these optional docs
if (Test-Path $paths.RESEARCH) { $docs += 'research.md' }
if (Test-Path $paths.DATA_MODEL) { $docs += 'data-model.md' }

# Check contracts directory (only if it exists and has files)
if ((Test-Path $paths.CONTRACTS_DIR) -and (Get-ChildItem -Path $paths.CONTRACTS_DIR -ErrorAction SilentlyContinue | Select-Object -First 1)) { 
    $docs += 'contracts/' 
}

if (Test-Path $paths.QUICKSTART) { $docs += 'quickstart.md' }

# Include tasks.md if requested and it exists
if ($IncludeTasks -and (Test-Path $paths.TASKS)) { 
    $docs += 'tasks.md' 
}

# Output results
if ($Json) {
    # JSON output
    [PSCustomObject]@{ 
        FEATURE_DIR = $paths.FEATURE_DIR
        AVAILABLE_DOCS = $docs 
    } | ConvertTo-Json -Compress
} else {
    # Text output
    Write-Output "FEATURE_DIR:$($paths.FEATURE_DIR)"
    Write-Output "AVAILABLE_DOCS:"
    
    # Show status of each potential document
    Test-FileExists -Path $paths.RESEARCH -Description 'research.md' | Out-Null
    Test-FileExists -Path $paths.DATA_MODEL -Description 'data-model.md' | Out-Null
    Test-DirHasFiles -Path $paths.CONTRACTS_DIR -Description 'contracts/' | Out-Null
    Test-FileExists -Path $paths.QUICKSTART -Description 'quickstart.md' | Out-Null
    
    if ($IncludeTasks) {
        Test-FileExists -Path $paths.TASKS -Description 'tasks.md' | Out-Null
    }
}

if ($depsMissing) { exit 1 }
