---
description: Run Phase 0 SELECT to score ideas using AI-RICE and pick a winner.
scripts:
  sh: "scripts/bash/state-check.sh ideate"
  ps: "scripts/powershell/state-check.ps1 -RequiredPhase ideate"
agent_scripts:
  sh: "scripts/bash/validate-airice.sh"
  ps: "scripts/powershell/validate-airice.ps1"
---

# /speckit.select - SELECT Phase

## Instructions

<!--EXECUTION_FLOW
1. If state.yaml missing, run state-reconstruct.{sh|ps} and confirm IDEATE is complete.
2. If SELECT already completed, warn and offer: Overwrite / Append / Cancel.
   - Overwrite: delete .spec-kit/idea_selection.md and downstream artifacts (ai_vision_canvas.md, vision_brief.md, approvals/g0-validation-report.md) then re-run.
   - Append: keep existing report and add a new "Revision" section with updated scoring.
   - Cancel: exit without changes.
3. Ensure IDEATE completed (state-check).
4. Load ideas from .spec-kit/ideas_backlog.md.
5. Score each idea using AI-RICE (Reach, Impact, Confidence, Data_Readiness, Effort, Risk).
6. Calculate AI-RICE score: (Reach * Impact * Confidence * Data_Readiness) / (Effort * Risk).
7. Identify top-scoring idea; include runner-ups.
8. Write .spec-kit/idea_selection.md using idea-selection-template.md.
9. Validate AI-RICE completeness with validate-airice.{sh|ps}.
10. Update state: set current_phase=structure; record idea_selection path.
11. Report completion and selected idea.
-->

## Required Inputs

- ideas_backlog.md (from IDEATE)

## Output

- `.spec-kit/idea_selection.md`
- Update `.spec-kit/state.yaml`

## RICE Reference (Base)

RICE uses four factors to score initiatives:
- Reach: how many people are impacted in a given period
- Impact: the impact per person
- Confidence: how confident you are in the estimates
- Effort: how much work is required

AI-RICE extends RICE by adding Data_Readiness and Risk.

## Completion Criteria

- All ideas scored on 6 dimensions
- Score formula applied consistently
- Winner + runner-ups documented
- Validator passes
