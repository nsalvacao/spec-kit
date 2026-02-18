# detect-phase0.ps1 — Detect if Phase 0 was used in this project
#
# Exit 0 if Phase 0 is detected (ideation, selection, or structure completed)
# Exit 1 if Phase 0 was not used
#
# Detection strategy (Option B with Option A fallback):
#   1. Parse .spec-kit/state.yaml for phases_completed entries
#   2. Fallback: check for non-empty .spec-kit/ideation/ directory
#
# Usage:
#   .\detect-phase0.ps1               # silent — use exit code
#   .\detect-phase0.ps1 -Verbose      # print reason to stdout
#   .\detect-phase0.ps1 -Json         # output JSON result

param(
    [Alias('v')]
    [switch]$Verbose,
    [switch]$Json,
    [switch]$Help
)

if ($Help) {
    Write-Host "Usage: detect-phase0.ps1 [-Verbose] [-Json]"
    Write-Host ""
    Write-Host "Detects whether Phase 0 (AI System Ideation) was used in this project."
    Write-Host ""
    Write-Host "Exit codes:"
    Write-Host "  0  Phase 0 detected"
    Write-Host "  1  Phase 0 not detected"
    exit 0
}

$stateFile   = '.spec-kit/state.yaml'
$ideationDir = '.spec-kit/ideation'

# ─── Option B: Parse state.yaml ──────────────────────────────────────────────

if ((Test-Path $stateFile) -and (Get-Command python3 -ErrorAction SilentlyContinue)) {
    $pythonCode = @'
import yaml, sys, json

with open(sys.argv[1], 'r') as f:
    data = yaml.safe_load(f) or {}

phases = data.get('phases_completed', []) or []
phase0_phases = ['ideate', 'ideation', 'selection', 'structure']
found = [p for p in phases if p in phase0_phases]

print(json.dumps({
    "phase0": len(found) > 0,
    "method": "state",
    "phases": found
}))
'@

    try {
        $result = python3 -c $pythonCode $stateFile 2>$null
        if ($LASTEXITCODE -eq 0 -and $result) {
            $data = $result | ConvertFrom-Json
            if ($data.phase0) {
                if ($Json) {
                    Write-Output $result
                } elseif ($Verbose) {
                    $phaseList = ($data.phases -join ', ')
                    Write-Host "Phase 0 detected (state.yaml): phases_completed includes [$phaseList]"
                }
                exit 0
            }
        }
    } catch {
        # Python parse failed — fall through to Option A
    }
}

# ─── Option A: Fallback — check .spec-kit/ideation/ directory ────────────────

if (Test-Path $ideationDir) {
    $files = Get-ChildItem -Path $ideationDir -Recurse -File -Depth 2 |
             Where-Object { $_.Name -notlike '.*' }
    $fileCount = ($files | Measure-Object).Count

    if ($fileCount -gt 0) {
        if ($Json) {
            Write-Output "{`"phase0`":true,`"method`":`"directory`",`"phases`":[],`"files`":$fileCount}"
        } elseif ($Verbose) {
            Write-Host "Phase 0 detected (directory fallback): $ideationDir contains $fileCount file(s)"
        }
        exit 0
    }
}

# ─── Not detected ────────────────────────────────────────────────────────────

if ($Json) {
    Write-Output '{"phase0":false,"method":"none","phases":[]}'
} elseif ($Verbose) {
    Write-Host "Phase 0 not detected"
}
exit 1
