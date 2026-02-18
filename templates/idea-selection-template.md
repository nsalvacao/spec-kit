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
- Idea IDs in the table MUST link to the corresponding heading anchor in ideas_backlog.md.
  Anchor derivation: take the text after "### Idea ", lowercase it, replace spaces with hyphens,
  drop other punctuation (GFM drops parentheses, colons, etc.).
  Examples: "Idea S1" → anchor suffix "s1" → full anchor #idea-s1
            "Idea SC1-Substitute" → suffix "sc1-substitute" → #idea-sc1-substitute
            "Idea Beta (v2)" → suffix "beta-v2" → #idea-beta-v2
  In the link template, [IDEA_ID_ANCHOR] is ONLY the derived suffix (e.g. "s1"),
  NOT the full anchor string (the "#idea-" prefix is already in the link path).
- Input dimension guidelines:
  - Reach: number of users/sessions impacted in a consistent time window (e.g. per quarter).
            Anchor examples: 100 (niche), 1 000 (small), 10 000 (medium), 100 000+ (large).
  - Impact: use 0.25 (minimal), 0.5 (low), 1.0 (normal), 2.0 (high), 3.0 (massive).
  - Confidence: 0-100% (enter as decimal in formula: 70% → 0.70).
  - Data_Readiness: 0-100% (enter as decimal in formula: 80% → 0.80).
  - Effort: person-weeks. Anchor examples: 1 (days), 4 (1 month), 12 (1 quarter), 26+ (6 months).
  - Risk: 1-10 (higher = riskier). 1-3 low, 4-6 medium, 7-10 high.
- Norm_Score = (AI-RICE_raw / session_max_raw) * 100, rounded to 1 decimal.
  session_max_raw = highest raw AI-RICE score among all ideas evaluated in this session.
  The best idea always scores 100; all others are relative to it.
- Score interpretation: 70-100 = Strong candidate; 40-69 = Viable; 0-39 = Weak.
-->

## AI-RICE Scoring Table

| Idea ID | Reach | Impact | Confidence | Data_Readiness | Effort | Risk | AI-RICE Score | Norm_Score |
| --------- | ------- | -------- | ------------ | ---------------- | -------- | ------ | --------------- | ---------- |
| [IDEA_ID_1](.spec-kit/ideas_backlog.md#idea-[IDEA_ID_1_ANCHOR]) | [reach] | [impact] | [conf%] | [dr%] | [effort] | [risk] | [score] | [norm] |
| [IDEA_ID_2](.spec-kit/ideas_backlog.md#idea-[IDEA_ID_2_ANCHOR]) | [reach] | [impact] | [conf%] | [dr%] | [effort] | [risk] | [score] | [norm] |
| ... | ... | ... | ... | ... | ... | ... | ... | ... |

**Formula**: (Reach \* Impact \* Confidence \* Data_Readiness) / (Effort \* Risk)

**Normalization**: Norm\_Score = (AI-RICE\_raw / session\_max\_raw) × 100

## Selected Idea

**ID**: [IDEA_ID](.spec-kit/ideas_backlog.md#idea-[IDEA_ID_ANCHOR])
**Text**: [Idea description]
**Tag**: [SEED | SCAMPER-<Lens> | HMW-<Dimension>]
**AI-RICE Score**: [raw score] (Norm: [Norm_Score]/100)

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

### 2nd Place: [IDEA_ID](.spec-kit/ideas_backlog.md#idea-[IDEA_ID_ANCHOR])

- Score: [raw score] (Norm: [Norm_Score]/100)
- Why it is a strong alternative

### 3rd Place: [IDEA_ID](.spec-kit/ideas_backlog.md#idea-[IDEA_ID_ANCHOR])

- Score: [raw score] (Norm: [Norm_Score]/100)
- Why it is a strong alternative

## Risk Note

> **Risk mitigations are defined in the STRUCTURE phase**, not here.
>
> The **Risk** dimension above (1–10 scale) feeds the AI-RICE score to inform selection.
> Concrete mitigations, owners, and controls are documented in:
>
> - `ai_vision_canvas.md` → Component 16: Safety & Risk (created in STRUCTURE)
> - `approvals/g0-validation-report.md` → Criterion Q5: Risk mitigations defined (validated in VALIDATE)
