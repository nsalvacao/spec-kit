---
description: Run Phase 0 STRUCTURE to complete the Integrated Canvas and produce a vision brief.
scripts:
  sh: "scripts/bash/state-check.sh select"
  ps: "scripts/powershell/state-check.ps1 -RequiredPhase select"
scaffold_scripts:
  sh: "scripts/bash/structure.sh"
  ps: "scripts/powershell/structure.ps1"
agent_scripts:
  sh: "scripts/bash/validate-canvas.sh"
  ps: "scripts/powershell/validate-canvas.ps1"
---

# /speckit.structure - STRUCTURE Phase

## Instructions

<!--EXECUTION_FLOW
1. If state.yaml missing, run state-reconstruct.{sh|ps} and confirm SELECT is complete.
2. If STRUCTURE already completed, warn and offer: Overwrite / Append / Cancel.
   - Overwrite: delete ai_vision_canvas.md, vision_brief.md, approvals/g0-validation-report.md then re-run.
   - Append: keep existing artifacts and add a "Revision" section to the vision brief.
   - Cancel: exit without changes.
3. Ensure SELECT completed (state-check).
4. If .spec-kit/ai_vision_canvas.md does not exist, scaffold it:
   - Run: `bash scripts/bash/structure.sh [PROJECT_DIR]` (Linux/macOS)
   - Or:  `pwsh scripts/powershell/structure.ps1 [-ProjectDir PROJECT_DIR]` (Windows)
5. Load selected idea from .spec-kit/idea_selection.md.
6. Fill Integrated Canvas (JTBD + Lean + AI) using ai-vision-canvas-template.md.
7. Validate canvas completeness with validate-canvas.{sh|ps}.
8. Transform canvas into vision_brief.md using vision-brief-template.md.
9. Update state: set current_phase=validate; record ai_vision_canvas and vision_brief paths.
10. Report completion and handoff readiness.
-->

## Required Inputs

- idea_selection.md (selected idea)

## Output

- `.spec-kit/ai_vision_canvas.md`
- `.spec-kit/vision_brief.md`
- Update `.spec-kit/state.yaml`

## Framework Reference

- JTBD focuses on the job (progress) in a specific context.
- Lean Startup uses hypotheses and validated learning (Build-Measure-Learn).
- AI risk and safety should be considered explicitly (e.g., trustworthy AI characteristics).

## Completion Criteria

- All 18 canvas components completed
- Job statement follows When/Want/So format
- Validation passes
