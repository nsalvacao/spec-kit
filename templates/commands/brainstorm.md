---
description: Run strategic BRAINSTORM to produce a deep expansion artifact that feeds Phase 0 IDEATE.
scripts:
  sh: "scripts/bash/brainstorm.sh"
  ps: "scripts/powershell/brainstorm.ps1"
agent_scripts:
  sh: "scripts/bash/validate-brainstorm.sh"
  ps: "scripts/powershell/validate-brainstorm.ps1"
---

# /speckit.brainstorm - STRATEGY Phase

## Instructions

<!--EXECUTION_FLOW
1. Ensure the project context is understood before ideation:
   - Read README and key docs/code to identify real asset, domain, and moat.
2. If .ideas/brainstorm-expansion.md does not exist, scaffold it:
   - Run: `bash scripts/bash/brainstorm.sh [PROJECT_DIR]` (Linux/macOS)
   - Or:  `pwsh scripts/powershell/brainstorm.ps1 [-ProjectDir PROJECT_DIR]` (Windows)
3. Produce a complete strategic brainstorm document with all required sections:
   - Real Asset
   - SCAMPER
   - Divergent ideation (20+ ideas)
   - Convergent tier ranking
   - Blue Ocean
   - TAM/SAM/SOM
   - Jobs-to-be-Done
   - Flywheel
   - One-line pitches
   - Honest weaknesses and risks
   - Monday Morning actions
4. Validate depth/structure with validate-brainstorm.{sh|ps}.
5. Keep the artifact private under `.ideas/` (gitignored by default).
6. Handoff to `/speckit.ideate`: use this artifact as context to generate stronger seeds for AI-RICE.
-->

## Required Inputs

- Project context (README + relevant source/docs)

## Output

- `.ideas/brainstorm-expansion.md`

## Position in workflow

- This command complements Phase 0 and does not replace it.
- Recommended sequence:
  - `/speckit.brainstorm` -> `/speckit.ideate` -> `/speckit.select` -> `/speckit.structure` -> `/speckit.validate`
