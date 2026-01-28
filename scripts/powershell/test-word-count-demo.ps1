#!/usr/bin/env pwsh
# Demonstration script for Issue #41: G0 Validator Word Count Logic
# This script demonstrates that the validator correctly counts words in the Model Approach section
# regardless of formatting (single-line vs multi-line paragraphs)

$ErrorActionPreference = 'Stop'

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$validator = Join-Path $scriptDir 'validate-g0.ps1'
$tmpDir = Join-Path ([System.IO.Path]::GetTempPath()) ([System.IO.Path]::GetRandomFileName())
New-Item -ItemType Directory -Path $tmpDir | Out-Null

function Cleanup {
    if (Test-Path $tmpDir) {
        Remove-Item -Path $tmpDir -Recurse -Force
    }
}

try {
    Write-Host '=============================================='
    Write-Host 'G0 Validator Word Count Demonstration'
    Write-Host 'Issue #41: Validator should count ALL words'
    Write-Host '=============================================='
    Write-Host ''

    # Test Case 1: Single-line paragraph with 100+ words
    Write-Host 'Test Case 1: Single-line paragraph (100+ words)'
    Write-Host '----------------------------------------------'
    $test1File = Join-Path $tmpDir 'test1_vision_brief.md'
    @'
---
artifact: vision_brief
---
# Vision Brief: Test System

## One-Liner
Test system for validator.
**Canvas References**: C7

## Problem Statement
**Job-to-be-Done**: When testing, I want validation, so I can ensure quality.
**Canvas References**: C1

## Solution Approach
Test solution.
**Canvas References**: C7

## Success Criteria
1. Metric 1
2. Metric 2
3. Metric 3
**Canvas References**: C10

## Key Assumptions
| Assumption | Validation Method | Risk If Wrong | Tracking |
|------------|-------------------|---------------|----------|
| Assumption1 | Method1 | Risk1 | Track1 |
| Assumption2 | Method2 | Risk2 | Track2 |
| Assumption3 | Method3 | Risk3 | Track3 |
**Canvas References**: C8

## Data & Model Strategy
**Data Requirements**: Test data.
- Test source (100% ready)

**Model Approach**: Word01 Word02 Word03 Word04 Word05 Word06 Word07 Word08 Word09 Word10 Word11 Word12 Word13 Word14 Word15 Word16 Word17 Word18 Word19 Word20 Word21 Word22 Word23 Word24 Word25 Word26 Word27 Word28 Word29 Word30 Word31 Word32 Word33 Word34 Word35 Word36 Word37 Word38 Word39 Word40 Word41 Word42 Word43 Word44 Word45 Word46 Word47 Word48 Word49 Word50 Word51 Word52 Word53 Word54 Word55 Word56 Word57 Word58 Word59 Word60 Word61 Word62 Word63 Word64 Word65 Word66 Word67 Word68 Word69 Word70 Word71 Word72 Word73 Word74 Word75 Word76 Word77 Word78 Word79 Word80 Word81 Word82 Word83 Word84 Word85 Word86 Word87 Word88 Word89 Word90 Word91 Word92 Word93 Word94 Word95 Word96 Word97 Word98 Word99 Word100

**Evaluation**: Test metrics.
**Canvas References**: C13

## Constraints & Risks
Test constraints.
**Canvas References**: C16
'@ | Set-Content -Path $test1File -NoNewline

    $output = & $validator -FilePath $test1File 2>&1 | Out-String
    if ($output -match 'Gate G0 automated checks passed') {
        Write-Host '✓ PASS: Single-line paragraph validated successfully' -ForegroundColor Green
        Write-Host '  (100 words counted correctly)'
    } else {
        Write-Host '✗ FAIL: Single-line paragraph validation failed' -ForegroundColor Red
        Write-Host $output
        exit 1
    }
    Write-Host ''

    # Test Case 2: Multi-line paragraph (41 words + 59 words)
    Write-Host 'Test Case 2: Multi-line paragraph split across lines'
    Write-Host '----------------------------------------------'
    $test2File = Join-Path $tmpDir 'test2_vision_brief.md'
    @'
---
artifact: vision_brief
---
# Vision Brief: Test System

## One-Liner
Test system for validator.
**Canvas References**: C7

## Problem Statement
**Job-to-be-Done**: When testing, I want validation, so I can ensure quality.
**Canvas References**: C1

## Solution Approach
Test solution.
**Canvas References**: C7

## Success Criteria
1. Metric 1
2. Metric 2
3. Metric 3
**Canvas References**: C10

## Key Assumptions
| Assumption | Validation Method | Risk If Wrong | Tracking |
|------------|-------------------|---------------|----------|
| Assumption1 | Method1 | Risk1 | Track1 |
| Assumption2 | Method2 | Risk2 | Track2 |
| Assumption3 | Method3 | Risk3 | Track3 |
**Canvas References**: C8

## Data & Model Strategy
**Data Requirements**: Test data.
- Test source (100% ready)

**Model Approach**: Word01 Word02 Word03 Word04 Word05 Word06 Word07 Word08 Word09 Word10 Word11 Word12 Word13 Word14 Word15 Word16 Word17 Word18 Word19 Word20 Word21 Word22 Word23 Word24 Word25 Word26 Word27 Word28 Word29 Word30 Word31 Word32 Word33 Word34 Word35 Word36 Word37 Word38 Word39 Word40 Word41
Word42 Word43 Word44 Word45 Word46 Word47 Word48 Word49 Word50 Word51 Word52 Word53 Word54 Word55 Word56 Word57 Word58 Word59 Word60 Word61 Word62 Word63 Word64 Word65 Word66 Word67 Word68 Word69 Word70 Word71 Word72 Word73 Word74 Word75 Word76 Word77 Word78 Word79 Word80 Word81 Word82 Word83 Word84 Word85 Word86 Word87 Word88 Word89 Word90 Word91 Word92 Word93 Word94 Word95 Word96 Word97 Word98 Word99 Word100

**Evaluation**: Test metrics.
**Canvas References**: C13

## Constraints & Risks
Test constraints.
**Canvas References**: C16
'@ | Set-Content -Path $test2File -NoNewline

    $output = & $validator -FilePath $test2File 2>&1 | Out-String
    if ($output -match 'Gate G0 automated checks passed') {
        Write-Host '✓ PASS: Multi-line paragraph validated successfully' -ForegroundColor Green
        Write-Host '  (41 + 59 = 100 words counted correctly)'
    } else {
        Write-Host '✗ FAIL: Multi-line paragraph validation failed' -ForegroundColor Red
        Write-Host $output
        exit 1
    }
    Write-Host ''

    # Test Case 3: Multi-line with blank line in middle
    Write-Host 'Test Case 3: Multi-line paragraph with blank line'
    Write-Host '----------------------------------------------'
    $test3File = Join-Path $tmpDir 'test3_vision_brief.md'
    @'
---
artifact: vision_brief
---
# Vision Brief: Test System

## One-Liner
Test system for validator.
**Canvas References**: C7

## Problem Statement
**Job-to-be-Done**: When testing, I want validation, so I can ensure quality.
**Canvas References**: C1

## Solution Approach
Test solution.
**Canvas References**: C7

## Success Criteria
1. Metric 1
2. Metric 2
3. Metric 3
**Canvas References**: C10

## Key Assumptions
| Assumption | Validation Method | Risk If Wrong | Tracking |
|------------|-------------------|---------------|----------|
| Assumption1 | Method1 | Risk1 | Track1 |
| Assumption2 | Method2 | Risk2 | Track2 |
| Assumption3 | Method3 | Risk3 | Track3 |
**Canvas References**: C8

## Data & Model Strategy
**Data Requirements**: Test data.
- Test source (100% ready)

**Model Approach**: Word01 Word02 Word03 Word04 Word05 Word06 Word07 Word08 Word09 Word10 Word11 Word12 Word13 Word14 Word15 Word16 Word17 Word18 Word19 Word20 Word21 Word22 Word23 Word24 Word25 Word26 Word27 Word28 Word29 Word30 Word31 Word32 Word33 Word34 Word35 Word36 Word37 Word38 Word39 Word40 Word41

Word42 Word43 Word44 Word45 Word46 Word47 Word48 Word49 Word50 Word51 Word52 Word53 Word54 Word55 Word56 Word57 Word58 Word59 Word60 Word61 Word62 Word63 Word64 Word65 Word66 Word67 Word68 Word69 Word70 Word71 Word72 Word73 Word74 Word75 Word76 Word77 Word78 Word79 Word80 Word81 Word82 Word83 Word84 Word85 Word86 Word87 Word88 Word89 Word90 Word91 Word92 Word93 Word94 Word95 Word96 Word97 Word98 Word99 Word100

**Evaluation**: Test metrics.
**Canvas References**: C13

## Constraints & Risks
Test constraints.
**Canvas References**: C16
'@ | Set-Content -Path $test3File -NoNewline

    $output = & $validator -FilePath $test3File 2>&1 | Out-String
    if ($output -match 'Gate G0 automated checks passed') {
        Write-Host '✓ PASS: Paragraph with blank line validated successfully' -ForegroundColor Green
        Write-Host '  (100 words counted correctly despite blank line)'
    } else {
        Write-Host '✗ FAIL: Paragraph with blank line validation failed' -ForegroundColor Red
        Write-Host $output
        exit 1
    }
    Write-Host ''

    Write-Host '=============================================='
    Write-Host 'All tests passed! ✓' -ForegroundColor Green
    Write-Host '=============================================='
    Write-Host ''
    Write-Host 'Summary:'
    Write-Host '- The validator correctly counts words in single-line paragraphs'
    Write-Host '- The validator correctly counts words across multiple lines'
    Write-Host '- The validator correctly handles blank lines within paragraphs'
    Write-Host '- Word counting continues until the next ** subsection header'
    Write-Host ''
    Write-Host 'The PowerShell implementation reads ALL words in the Model'
    Write-Host 'Approach section, regardless of line breaks or formatting.'

} finally {
    Cleanup
}
