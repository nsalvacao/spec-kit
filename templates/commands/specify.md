---
description: Create or update the feature specification from a natural language feature description.
handoffs: 

  - label: Build Technical Plan
    agent: speckit.plan
    prompt: Create a plan for the spec. I am building with...

  - label: Clarify Spec Requirements
    agent: speckit.clarify
    prompt: Clarify specification requirements
    send: true
scripts:
  sh: scripts/bash/create-new-feature.sh --json "{ARGS}"
  ps: scripts/powershell/create-new-feature.ps1 -Json "{ARGS}"
---

## Role

Create or update a technology-agnostic feature specification from a natural language description, written for business stakeholders, not developers.

## Context Inputs

| Artifact | Path | Required |
|----------|------|----------|
| User description | `$ARGUMENTS` | ✅ Mandatory |
| Phase 0 canvas | `.spec-kit/ai_vision_canvas.md` | If exists — read first |
| Phase 0 selection | `.spec-kit/idea_selection.md` | If exists — read first |
| Strategy artifacts | `.ideas/brainstorm-expansion.md`, `.ideas/execution-plan.md` | If exists — read for context |
| Spec template | `templates/spec-template.md` | ✅ Mandatory |

> Phase 0 and `.ideas/` artifacts take precedence over inferences from README alone.

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty). The text after `/speckit.specify` **is** the feature description — do not ask the user to repeat it unless they provided an empty command.

## Execution Flow

1. **Validate input** — if `$ARGUMENTS` is empty: `ERROR "No feature description provided"`

2. **Generate branch short-name** (2-4 words, action-noun format):
   - Preserve technical terms (OAuth2, API, JWT)
   - Examples: "user-auth", "oauth2-api-integration", "fix-payment-timeout"

3. **Find next available branch number**:

   ```bash
   git fetch --all --prune
   # Search ALL feature branches (not just this short-name) to find the global highest number
   git ls-remote --heads origin | grep -E 'refs/heads/[0-9]+-'
   git branch | grep -E '^[* ]*[0-9]+-'
   ```

   Extract all numbers, take the highest across remote branches, local branches, and `specs/` directories. Use `highest_found + 1`; start at `1` if none found. Run `{SCRIPT}` exactly once:

   ```bash
   # Bash:  {SCRIPT} --json --number N --short-name "short-name" "Feature description"
   # PS:    {SCRIPT} -Json -Number N -ShortName "short-name" "Feature description"
   ```

   Parse `BRANCH_NAME` and `SPEC_FILE` from JSON output.

4. **Load** `templates/spec-template.md` to understand required sections.

5. **Draft specification** into `SPEC_FILE`:
   - Focus on **WHAT** and **WHY** — no tech stack, APIs, or code structure
   - Make informed guesses; document assumptions in the Assumptions section
   - Maximum **3 `[NEEDS CLARIFICATION]`** markers — only for decisions that significantly impact scope or UX with no reasonable default
   - Priority order for clarifications: scope > security/privacy > UX > technical details

6. **Validate spec** against quality checklist:
   - Write checklist to `FEATURE_DIR/checklists/requirements.md`
   - Check: no implementation details, all mandatory sections complete, requirements are testable, success criteria are measurable and tech-agnostic
   - If items fail: fix spec and re-validate (max 3 iterations); document remaining issues if still failing

7. **Resolve clarifications** (if any `[NEEDS CLARIFICATION]` markers remain):
   - Keep only top 3 by impact; make informed guesses for the rest
   - Present each as a structured question with 3 options + custom
   - Wait for user responses → update spec → re-validate

8. **Report completion**: branch name, spec file path, checklist results, readiness for `/speckit.clarify` or `/speckit.plan`.

## Input / Output Specification

**Input**: Natural language feature description (free text)

**Output**:

| Artifact | Path | Description |
|----------|------|-------------|
| Feature spec | `specs/N-short-name/spec.md` | Completed specification |
| Quality checklist | `specs/N-short-name/checklists/requirements.md` | Validation results |

**Script contract**: `{SCRIPT}` creates the branch and initialises `SPEC_FILE` before writing. Run exactly once per feature.

## Error Scenarios

| Condition | Detection | Action |
|-----------|-----------|--------|
| Empty feature description | `$ARGUMENTS` is blank | `ERROR "No feature description provided"` — halt |
| Cannot determine user scenarios | No clear user flow in description | `ERROR "Cannot determine user scenarios"` — halt |
| Script fails | Non-zero exit from `{SCRIPT}` | Report error with stderr; do not proceed |
| Validation fails after 3 iterations | Items still failing after 3 fix cycles | Document issues in checklist notes; warn user |
| Quote conflict in args | Single quotes in description | Escape: `'I'\''m Groot'` or use double quotes |

## Success Criteria Guidelines

Success criteria must be measurable, technology-agnostic, user-focused, and verifiable:

✅ Good: `"Users can complete checkout in under 3 minutes"`, `"System supports 10,000 concurrent users"`

❌ Bad: `"API response time under 200ms"` (technical), `"React components render efficiently"` (framework-specific)
