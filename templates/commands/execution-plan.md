---
description: Generate a strategic execution plan artifact that operationalizes roadmap and risk decisions.
scripts:
  sh: "scripts/bash/execution-plan.sh"
  ps: "scripts/powershell/execution-plan.ps1"
agent_scripts:
  sh: "scripts/bash/validate-execution-plan.sh"
  ps: "scripts/powershell/validate-execution-plan.ps1"
---

# /speckit.execution-plan - STRATEGY Phase

## Instructions

<!--EXECUTION_FLOW
1. Read context before planning:
   - If present, read `.ideas/brainstorm-expansion.md` first.
   - Read README and relevant docs/code to ground decisions.
2. If `.ideas/execution-plan.md` does not exist, scaffold it:
   - Run: `bash scripts/bash/execution-plan.sh [PROJECT_DIR]` (Linux/macOS)
   - Or:  `pwsh scripts/powershell/execution-plan.ps1 [-ProjectDir PROJECT_DIR]` (Windows)
3. Produce a complete execution plan with all required sections:
   - second-order effects and dependencies
   - roadmap and impact matrix
   - pre-mortem and moat assessment
   - risk register and growth strategy
   - contrarian challenges
4. Validate depth/structure with validate-execution-plan.{sh|ps}.
5. Keep the artifact private under `.ideas/` (gitignored by default).
6. Handoff to `/speckit.strategic-review` when available:
   - execution-plan is the planning artifact
   - strategic-review is the readiness scoring and blocker extraction gate
-->

## Required Inputs

- Project context (README + relevant source/docs)
- Optional strategic context from `.ideas/brainstorm-expansion.md`

## Output

- `.ideas/execution-plan.md`

## Position in workflow

- This command complements Phase 0 and does not replace it.
- Recommended sequence:
  - `/speckit.brainstorm` -> `/speckit.ideate` -> `/speckit.select` -> `/speckit.structure` -> `/speckit.validate` -> `/speckit.execution-plan`
