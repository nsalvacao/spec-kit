---
description: Run a pre-launch strategic readiness review with weighted scoring and blocker extraction.
scripts:
  sh: "scripts/bash/strategic-review.sh"
  ps: "scripts/powershell/strategic-review.ps1"
agent_scripts:
  sh: "scripts/bash/validate-strategic-review.sh"
  ps: "scripts/powershell/validate-strategic-review.ps1"
---

# /speckit.strategic-review - STRATEGY Quality Gate

## Instructions

<!--EXECUTION_FLOW
1. Load strategic context before scoring:
   - Read `.ideas/brainstorm-expansion.md` if present.
   - Read `.ideas/execution-plan.md` if present.
   - Read README and key outputs to be exposed publicly.
2. If `.ideas/evaluation-results.md` does not exist, scaffold it:
   - Run: `bash scripts/bash/strategic-review.sh [PROJECT_DIR]` (Linux/macOS)
   - Or:  `pwsh scripts/powershell/strategic-review.ps1 [-ProjectDir PROJECT_DIR]` (Windows)
3. Complete all review sections and scorecard values with concrete evidence.
4. Validate with `validate-strategic-review.{sh|ps}`:
   - validates structure and score coherence,
   - applies configured thresholds from `.specify/spec-kit.yml`,
   - emits `.ideas/launch-blockers.md` for configured failing bands.
5. Keep artifacts private under `.ideas/` (gitignored by default).
-->

## Required Inputs

- Project outputs and README/documentation
- Optional strategic artifacts:
  - `.ideas/brainstorm-expansion.md`
  - `.ideas/execution-plan.md`

## Output

- `.ideas/evaluation-results.md`
- `.ideas/launch-blockers.md` (conditional based on configured score bands)

## Position in workflow

- This command is a strategic quality gate and does not replace Phase 0 or SDD steps.
- Recommended sequence:
  - `/speckit.brainstorm` -> `/speckit.execution-plan` -> `/speckit.ideate` -> `/speckit.select` -> `/speckit.structure` -> `/speckit.validate` -> `/speckit.specify` -> `/speckit.plan` -> `/speckit.tasks` -> `/speckit.implement` -> `/speckit.strategic-review`
