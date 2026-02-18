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
1. Ensure IDEATE completed (state-check).
2. Load ideas from .spec-kit/ideas_backlog.md.
3. Score each idea using AI-RICE (Reach, Impact, Confidence, Data_Readiness, Effort, Risk).
4. Calculate AI-RICE score: (Reach * Impact * Confidence * Data_Readiness) / (Effort * Risk).
5. Identify top-scoring idea; include runner-ups.
6. Write .spec-kit/idea_selection.md using idea-selection-template.md.
   - For every Idea ID in the table and in Selected/Runner-Up sections, generate a markdown
     link to the corresponding heading anchor in ideas_backlog.md.
   - Anchor derivation: take text after "### Idea ", lowercase it, replace spaces with hyphens,
     drop other punctuation (GFM drops parentheses, colons, dots, etc.).
     Examples: "Idea S1" → suffix "s1" → #idea-s1
               "Idea SC1-Substitute" → suffix "sc1-substitute" → #idea-sc1-substitute
               "Idea Beta (v2)" → suffix "beta-v2" → #idea-beta-v2
   - [IDEA_ID_ANCHOR] in the link is ONLY the derived suffix; the "#idea-" prefix is hardcoded.
   - Link format: [IDEA_ID](.spec-kit/ideas_backlog.md#idea-<anchor-suffix>)
   - After computing raw AI-RICE scores, derive Norm_Score for each idea:
     Norm_Score = round((raw_score / session_max_raw) * 100, 1)
     where session_max_raw = highest raw score in this session (top idea = 100.0).
   - Interpretation thresholds: 70-100 Strong; 40-69 Viable; 0-39 Weak.
7. Validate AI-RICE completeness with validate-airice.{sh|ps}.
8. Update state: set current_phase=structure; record idea_selection path.
9. Report completion and selected idea.
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
- **Note**: Risk mitigations are NOT defined here; they belong in STRUCTURE (canvas component 16) and are validated in VALIDATE (G0 criterion Q5).
