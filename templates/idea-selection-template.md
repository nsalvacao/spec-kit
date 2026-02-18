---
artifact: idea_selection
phase: select
schema_version: "1.0"
generated: [ISO_8601_TIMESTAMP]
ideas_evaluated: [COUNT]
selected_idea_id: [IDEA_ID]
derived_from: .spec-kit/ideas_backlog.md
enables: .spec-kit/ai_vision_canvas.md
---

# Idea Selection Report

**Generated**: [ISO_8601_TIMESTAMP]
**Ideas Evaluated**: [COUNT]
**Source Backlog**: [ideas_backlog.md](.spec-kit/ideas_backlog.md)

<!--
Guidance:

- AI-RICE is based on RICE (Reach, Impact, Confidence, Effort).
- AI-RICE adds Data_Readiness and Risk.
- Use consistent time window for Reach (e.g., per quarter).
- Impact can use a 0.25-3 scale.
- Confidence should be a percentage (0-100).
- Effort is person-weeks.
- Risk is 1-10 (higher = riskier).
- Data_Readiness is 0-100%.
- Idea IDs in the table MUST link to the corresponding heading anchor in ideas_backlog.md.
  Anchor format: lowercase, spaces→hyphens, e.g. "Idea S1" → #idea-s1
-->

## AI-RICE Scoring Table

| Idea ID | Reach | Impact | Confidence | Data_Readiness | Effort | Risk | AI-RICE Score |
| --------- | ------- | -------- | ------------ | ---------------- | -------- | ------ | --------------- |
| [S1](.spec-kit/ideas_backlog.md#idea-s1) | 1000 | 2.0 | 70% | 80% | 4 | 3 | 93.3 |
| [SC1-Substitute](.spec-kit/ideas_backlog.md#idea-sc1-substitute) | 1500 | 1.5 | 60% | 50% | 6 | 5 | 37.5 |
| ... | ... | ... | ... | ... | ... | ... | ... |

**Formula**: (Reach \* Impact \* Confidence \* Data_Readiness) / (Effort \* Risk)

## Selected Idea

**ID**: [[IDEA_ID]](.spec-kit/ideas_backlog.md#idea-[IDEA_ID_ANCHOR])
**Text**: [Idea description]
**Tag**: [SEED | SCAMPER-<Lens> | HMW-<Dimension>]
**AI-RICE Score**: [Score]

### Dimensional Breakdown

- **Reach**: [value] - [rationale]
- **Impact**: [value] - [rationale]
- **Confidence**: [value] - [rationale]
- **Data_Readiness**: [value] - [rationale]
- **Effort**: [value] - [rationale]
- **Risk**: [value] - [rationale]

## Selection Rationale

[Why this idea scored highest; trade-offs vs runner-ups.]

## Runner-Ups (Pivot Options)

### 2nd Place: [[IDEA_ID]](.spec-kit/ideas_backlog.md#idea-[IDEA_ID_ANCHOR])

- Score: [value]
- Why it is a strong alternative

### 3rd Place: [[IDEA_ID]](.spec-kit/ideas_backlog.md#idea-[IDEA_ID_ANCHOR])

- Score: [value]
- Why it is a strong alternative

## Risk Note

> **Risk mitigations are defined in the STRUCTURE phase**, not here.
>
> The **Risk** dimension above (1–10 scale) feeds the AI-RICE score to inform selection.
> Concrete mitigations, owners, and controls are documented in:
>
> - `ai_vision_canvas.md` → Component 16: Safety & Risk (created in STRUCTURE)
> - `approvals/g0-validation-report.md` → Criterion Q5: Risk mitigations defined (validated in VALIDATE)
