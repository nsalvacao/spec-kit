---
description: Run Phase 0 VALIDATE to execute Gate G0 checks and produce a validation report.
scripts:
  sh: "scripts/bash/state-check.sh structure"
  ps: "scripts/powershell/state-check.ps1 -RequiredPhase structure"
agent_scripts:
  sh: "scripts/bash/validate-g0.sh"
  ps: "scripts/powershell/validate-g0.ps1"
---

# /speckit.validate - VALIDATE Phase

## Instructions

<!--EXECUTION_FLOW
1. If state.yaml missing, run state-reconstruct.{sh|ps} and confirm STRUCTURE is complete.
2. If VALIDATE already completed, warn and offer: Overwrite / Append / Cancel.
   - Overwrite: delete approvals/g0-validation-report.md and re-run validation.
   - Append: keep existing report and add a new validation entry (revision) with timestamp.
   - Cancel: exit without changes.
3. Ensure STRUCTURE completed (state-check).
4. Load .spec-kit/vision_brief.md and .spec-kit/ai_vision_canvas.md.
5. Run validate-g0.{sh|ps} (8 automated checks).
6. Complete 12 manual checks (Quality, AI-specific, Consistency).
7. Calculate overall score (X/20) and status.
8. If <18/20 or failures, capture waivers (justification + risk + mitigation + tracking).
9. Generate .spec-kit/approvals/g0-validation-report.md using g0-validation-report-template.md.
10. Update state: set current_phase=validate; record g0_validation_report path; add validate to phases_completed.
11. Report decision: PASS / PASS WITH WAIVER / FAIL. If PASS, handoff to /speckit.constitution.
-->

## Required Inputs

- `.spec-kit/vision_brief.md`
- `.spec-kit/ai_vision_canvas.md`

## Output

- `.spec-kit/approvals/g0-validation-report.md`
- Update `.spec-kit/state.yaml`

## Framework Reference

- Lean Startup: use validated learning to confirm assumptions.
- NIST AI RMF: consider risk, evaluation, and safety for trustworthy AI.

## Completion Criteria

- 20 criteria assessed (8 automated + 12 manual)
- Score calculated and status determined
- Waivers documented if applicable
- Report generated and state updated
