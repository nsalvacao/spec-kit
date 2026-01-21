---
description: Run Phase 0 IDEATE to generate the ideas backlog using SCAMPER + HMW.

# Script commands for generators

scripts:
  sh: "scripts/bash/state-init.sh"
  ps: "scripts/powershell/state-init.ps1"
agent_scripts:
  sh: "scripts/bash/validate-scamper.sh"
  ps: "scripts/powershell/validate-scamper.ps1"
---

# /speckit.ideate - IDEATE Phase

## Instructions

<!--EXECUTION_FLOW
1. If state.yaml missing, check for artifacts and run state-reconstruct.{sh|ps}; if none exist, run state-init.
2. If IDEATE already completed, warn and offer: Overwrite / Append / Cancel.
   - Overwrite: delete .spec-kit/ideas_backlog.md (destructive) before proceeding.
   - Append: keep existing backlog and add new ideas with provenance.
   - Cancel: exit without changes.
1. Collect 2-5 seed ideas (1-3 sentences each).
2. Apply SCAMPER (all 7 lenses) to each seed (one variation per lens).
3. Generate 5+ HMW questions across Data/Model/Safety/Cost/UX.
4. Write .spec-kit/ideas_backlog.md using ideas-backlog-template.md.
5. Validate with validate-scamper.{sh|ps}.
6. Update state: set current_phase=select; record ideas_backlog path.
7. Report completion and idea counts.
-->

## Required Inputs

- 2-5 seed AI system ideas (1-3 sentences each)

## Output

- `.spec-kit/ideas_backlog.md`
- Update `.spec-kit/state.yaml`

## Framework Reference

### SCAMPER (7 Lenses)

- Substitute
- Combine
- Adapt
- Modify
- Put to another use
- Eliminate
- Reverse

### HMW (How Might We)

Generate questions across:

- Data, Model, Safety, Cost, UX

## Completion Criteria

- All 7 SCAMPER lenses applied per seed
- 5+ HMW ideas
- Tags + provenance populated
- Validator passes
