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
-->

## AI-RICE Scoring Table

| Idea ID | Reach | Impact | Confidence | Data_Readiness | Effort | Risk | AI-RICE Score |
| --------- | ------- | -------- | ------------ | ---------------- | -------- | ------ | --------------- |
| S1 | 1000 | 2.0 | 70% | 80% | 4 | 3 | 93.3 |
| SC1-Substitute | 1500 | 1.5 | 60% | 50% | 6 | 5 | 37.5 |
| ... | ... | ... | ... | ... | ... | ... | ... |

**Formula**: (Reach \* Impact \* Confidence \* Data_Readiness) / (Effort \* Risk)

## Selected Idea

**ID**: [IDEA_ID]
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

### 2nd Place: [IDEA_ID]

- Score: [value]
- Why it is a strong alternative

### 3rd Place: [IDEA_ID]

- Score: [value]
- Why it is a strong alternative

## Risk Mitigation (Selected Idea)

| Risk | Mitigation | Owner | Notes |
| ------ | ------------ | ------- | ------- |
| [Risk] | [Mitigation] | [Owner] | [Notes] |
