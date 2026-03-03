# strategic-review.ps1 - Readiness review scaffold for strategic-review artifact.

param(
    [string]$ProjectDir = '',
    [switch]$Force,
    [switch]$Help
)

if ($Help) {
    Write-Output 'Usage: strategic-review.ps1 [[-ProjectDir] <path>] [-Force] [-Help]'
    Write-Output ''
    Write-Output 'Scaffold .ideas/evaluation-results.md for strategic launch readiness review.'
    Write-Output ''
    Write-Output 'Arguments:'
    Write-Output '  ProjectDir    Target project directory (default: current directory)'
    Write-Output ''
    Write-Output 'Options:'
    Write-Output '  -Force        Overwrite existing evaluation-results.md'
    Write-Output '  -Help         Show this help message'
    Write-Output ''
    Write-Output 'Next steps after running:'
    Write-Output '  1. Fill all TODO fields in .ideas/evaluation-results.md'
    Write-Output '  2. Complete scorecard values and action items'
    Write-Output '  3. Validate: scripts/powershell/validate-strategic-review.ps1 .ideas/evaluation-results.md'
    exit 0
}

function Test-ReparsePoint {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Path
    )

    if (-not (Test-Path -LiteralPath $Path)) {
        return $false
    }

    $item = Get-Item -LiteralPath $Path -Force
    return [bool]($item.Attributes -band [System.IO.FileAttributes]::ReparsePoint)
}

if (-not $ProjectDir) {
    $ProjectDir = (Get-Location).Path
}

if (-not (Test-Path -LiteralPath $ProjectDir -PathType Container)) {
    Write-Error "Error: Project directory does not exist: $ProjectDir"
    exit 1
}

$ProjectDir = (Resolve-Path -LiteralPath $ProjectDir).Path
$ProjectName = Split-Path -Leaf $ProjectDir
$ideasDir = Join-Path $ProjectDir '.ideas'
$target = Join-Path $ideasDir 'evaluation-results.md'
$timestamp = (Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ')

if ((Test-Path -LiteralPath $ideasDir) -and (Test-ReparsePoint -Path $ideasDir)) {
    Write-Error "Error: $ideasDir is a reparse point (symlink/junction). Remove it manually before proceeding."
    exit 1
}

if ((Test-Path -LiteralPath $ideasDir) -and -not (Test-Path -LiteralPath $ideasDir -PathType Container)) {
    Write-Error "Error: $ideasDir exists but is not a directory. Remove it manually before proceeding."
    exit 1
}

if ((Test-Path -LiteralPath $target) -and (Test-ReparsePoint -Path $target)) {
    Write-Error "Error: $target is a reparse point (symlink/junction). Remove it manually before proceeding."
    exit 1
}

if ((Test-Path -LiteralPath $target -PathType Container)) {
    Write-Error "Error: $target is a directory, not a file. Remove it manually before proceeding."
    exit 1
}

if ((Test-Path -LiteralPath $target) -and -not $Force) {
    Write-Error "Error: $target already exists. Use -Force to overwrite."
    exit 1
}

New-Item -ItemType Directory -Force -Path $ideasDir | Out-Null

$content = @"
---
artifact: evaluation_results
phase: strategy
schema_version: "1.0"
generated: $timestamp
derived_from:
  - .ideas/brainstorm-expansion.md
  - .ideas/execution-plan.md
enables: .ideas/launch-blockers.md
---

# $ProjectName -- Strategic Review (Pre-Launch Evaluation)

**Date:** $timestamp
**Overall Score:** TODO
**Band:** TODO
**Recommendation:** TODO

---

## 1. Output Quality Evaluation

TODO: Evaluate each relevant output with concrete evidence and summarize key risks.

## 2. Cross-Output Consistency

TODO: Document variance, bias patterns, and edge-case consistency gaps.

## 3. README Conversion Audit

TODO: Evaluate conversion-critical README elements and prioritize corrections.

## 4. Developer Experience Audit

TODO: Validate install, first-use flow, error quality, and help discoverability.

## 5. Security & Trust Audit

TODO: Verify secrets handling, subprocess safety, dependency posture, and attribution.

## 6. Competitive Positioning

TODO: Summarize competitor checks and positioning confidence before launch.

## 7. Launch Readiness Scorecard

| Category | Score (1-5) | Weight | Weighted |
| --- | --- | --- | --- |
| Output quality | TODO | 0.25 | TODO |
| README/docs quality | TODO | 0.20 | TODO |
| Developer experience | TODO | 0.20 | TODO |
| Security/trust | TODO | 0.15 | TODO |
| Competitive positioning | TODO | 0.10 | TODO |
| Test coverage | TODO | 0.10 | TODO |
| **TOTAL** | TODO | 1.00 | TODO |

## 8. Action Items

### Blockers (MUST fix)
1. TODO
2. TODO

### Improvements (SHOULD fix)
1. TODO
2. TODO

### Nice-to-Have (CAN fix)
1. TODO
2. TODO

## Appendix A - Evidence Log

TODO: Add concrete references (files, commands, outputs) supporting each score.

## Appendix B - Notes

TODO: Add assumptions, open questions, and deferred decisions.
"@

Set-Content -Path $target -Value $content -Encoding UTF8
Write-Output "Created: $target"
Write-Output ''
Write-Output 'Next steps:'
Write-Output '  1. Fill all TODO fields'
Write-Output '  2. Complete scorecard values and action-item sections'
Write-Output "  3. Validate: scripts/powershell/validate-strategic-review.ps1 $target"
