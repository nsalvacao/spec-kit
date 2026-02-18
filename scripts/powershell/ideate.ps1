# ideate.ps1 — Phase 0 IDEATE: scaffold ideas_backlog.md
#
# Creates .spec-kit/ideas_backlog.md from the standard SCAMPER + HMW template.
# Run this at the start of Phase 0 to begin the ideation process.
#
# Usage:
#   .\ideate.ps1 [[-ProjectDir] <path>] [-Force] [-Help]
#
# Examples:
#   .\ideate.ps1
#   .\ideate.ps1 C:\MyProject
#   .\ideate.ps1 -Force

param(
    [string]$ProjectDir = '',
    [switch]$Force,
    [switch]$Help
)

if ($Help) {
    Write-Output 'Usage: ideate.ps1 [[-ProjectDir] <path>] [-Force] [-Help]'
    Write-Output ''
    Write-Output 'Scaffold .spec-kit/ideas_backlog.md for Phase 0 ideation.'
    Write-Output ''
    Write-Output 'Arguments:'
    Write-Output '  ProjectDir    Target project directory (default: current directory)'
    Write-Output ''
    Write-Output 'Options:'
    Write-Output '  -Force        Overwrite existing ideas_backlog.md'
    Write-Output '  -Help         Show this help message'
    Write-Output ''
    Write-Output 'Next steps after running:'
    Write-Output '  1. Open .spec-kit/ideas_backlog.md and add 2-5 seed ideas'
    Write-Output '  2. Generate SCAMPER variations (7 per seed idea)'
    Write-Output '  3. Add HMW questions (5+ across Data/Model/Safety/Cost/UX)'
    Write-Output '  4. Run: validate-scamper.ps1 .spec-kit/ideas_backlog.md'
    exit 0
}

# Default to current directory
if (-not $ProjectDir) {
    $ProjectDir = (Get-Location).Path
}

# Validate project directory
if (-not (Test-Path $ProjectDir -PathType Container)) {
    Write-Error "Error: Project directory does not exist: $ProjectDir"
    exit 1
}

$ProjectDir = (Resolve-Path $ProjectDir).Path
$ProjectName = Split-Path -Leaf $ProjectDir
$specKitDir = Join-Path $ProjectDir '.spec-kit'
$target = Join-Path $specKitDir 'ideas_backlog.md'
$timestamp = (Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ')

# Check idempotency
if ((Test-Path $target -PathType Container)) {
    Write-Error "Error: $target is a directory, not a file. Remove it manually before proceeding."
    exit 1
}
if ((Test-Path $target) -and -not $Force) {
    Write-Error "Error: $target already exists. Use -Force to overwrite."
    exit 1
}

# Create .spec-kit directory
New-Item -ItemType Directory -Force -Path $specKitDir | Out-Null

# Write scaffolded ideas_backlog.md
$content = @"
---
artifact: ideas_backlog
phase: ideate
schema_version: "1.0"
generated: $timestamp
seed_count: 2  # Update this to match the actual number of seed ideas you add below
total_count: 2
derived_from: null
enables: .spec-kit/idea_selection.md
---

# Ideas Backlog: $ProjectName

**Generated**: $timestamp
**Seed Ideas**: 2
**Total Ideas**: 2

<!--
Guidance:

- SCAMPER uses seven lenses: Substitute, Combine, Adapt, Modify, Put to another use, Eliminate, Reverse.
- Each seed idea MUST produce one variation per lens (7 total).
- HMW (How Might We) questions should open the problem space; create 5+ across Data/Model/Safety/Cost/UX.
- Tags MUST use the format below to enable validators.
-->

## Seed Ideas (User-Provided)

<!-- Add 2-5 seed ideas. Use Tag: SEED only. -->

### Idea S1

**Text**: [1-3 sentence description of your first seed idea]
**Tag**: SEED
**Generated**: $timestamp

---

### Idea S2

**Text**: [1-3 sentence description of your second seed idea]
**Tag**: SEED
**Generated**: $timestamp

---

## SCAMPER Variations

<!--
Tag format: SCAMPER-<Lens>
Lens values (exact):

- Substitute
- Combine
- Adapt
- Modify
- Put-to-another-use
- Eliminate
- Reverse
Each variation MUST include Provenance linking to the originating seed idea.
-->

### Idea SC1-Substitute

**Text**: [How would you substitute a core component of S1?]
**Tag**: SCAMPER-Substitute
**Provenance**: Derived from Seed Idea S1
**Generated**: $timestamp

---

### Idea SC1-Combine

**Text**: [What could you combine with S1 to enhance it?]
**Tag**: SCAMPER-Combine
**Provenance**: Derived from Seed Idea S1
**Generated**: $timestamp

---

### Idea SC1-Adapt

**Text**: [How would you adapt S1 from another domain?]
**Tag**: SCAMPER-Adapt
**Provenance**: Derived from Seed Idea S1
**Generated**: $timestamp

---

### Idea SC1-Modify

**Text**: [What would you modify, magnify, or minify in S1?]
**Tag**: SCAMPER-Modify
**Provenance**: Derived from Seed Idea S1
**Generated**: $timestamp

---

### Idea SC1-Put-to-another-use

**Text**: [What other use could S1 serve?]
**Tag**: SCAMPER-Put-to-another-use
**Provenance**: Derived from Seed Idea S1
**Generated**: $timestamp

---

### Idea SC1-Eliminate

**Text**: [What could you eliminate from S1 to simplify it?]
**Tag**: SCAMPER-Eliminate
**Provenance**: Derived from Seed Idea S1
**Generated**: $timestamp

---

### Idea SC1-Reverse

**Text**: [What would happen if you reversed or rearranged S1?]
**Tag**: SCAMPER-Reverse
**Provenance**: Derived from Seed Idea S1
**Generated**: $timestamp

---

## HMW Questions (How Might We)

<!--
Generate 5+ HMW questions across these dimensions:
Data, Model, Safety, Cost, UX
Tag format: HMW-<Dimension>
-->

### Idea HMW1

**Text**: [HMW question about data quality or availability]
**Tag**: HMW-Data
**Provenance**: Generated from question "How might we improve data quality?"
**Generated**: $timestamp

---

### Idea HMW2

**Text**: [HMW question about model performance or accuracy]
**Tag**: HMW-Model
**Provenance**: Generated from question "How might we reduce hallucinations?"
**Generated**: $timestamp

---

### Idea HMW3

**Text**: [HMW question about safety or risk mitigation]
**Tag**: HMW-Safety
**Provenance**: Generated from question "How might we mitigate safety risks?"
**Generated**: $timestamp

---

### Idea HMW4

**Text**: [HMW question about cost or resource constraints]
**Tag**: HMW-Cost
**Provenance**: Generated from question "How might we control costs?"
**Generated**: $timestamp

---

### Idea HMW5

**Text**: [HMW question about user experience or adoption]
**Tag**: HMW-UX
**Provenance**: Generated from question "How might we improve UX?"
**Generated**: $timestamp

---
"@

Set-Content -Path $target -Value $content -Encoding UTF8
Write-Output "Created: $target"
Write-Output ''
Write-Output 'Next steps:'
Write-Output "  1. Open $target and fill in seed ideas and variations"
Write-Output '  2. Generate 7 SCAMPER variations per seed idea'
Write-Output '  3. Add 5+ HMW questions across Data/Model/Safety/Cost/UX'
Write-Output "  4. Validate: scripts/powershell/validate-scamper.ps1 $target"
