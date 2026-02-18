---
artifact: g0_validation_report
phase: validate
schema_version: "1.0"
generated: [ISO_8601_TIMESTAMP]
derived_from: .spec-kit/vision_brief.md
enables: .specify/spec.md
vision_brief: .spec-kit/vision_brief.md
overall_score: [X/20]
status: PASS | PASS WITH WAIVER | FAIL
decision: PROCEED | BLOCK
---

# Gate G0 Validation Report

**Generated**: [ISO_8601_TIMESTAMP]
**Vision Brief**: .spec-kit/vision_brief.md
**Overall Score**: [X/20] ([percentage]%)
**Status**: [PASS/PASS WITH WAIVER/FAIL]
**Decision**: [PROCEED/BLOCK]

<!--
Guidance:

- Automated checks are non-waivable. Manual checks may be waived with justification + risk + mitigation + tracking.
- Metrics should be SMART (Specific, Measurable, Achievable, Relevant, Time-bound).
- Validation should enable validated learning and risk-aware decisions before handoff.
-->

---

## Automated Checks (8 criteria)

| ID | Criterion | Status | Evidence |
| ---- | ----------- | -------- | ---------- |
| A1 | vision_brief.md exists | PASS/FAIL | [File found at path] |
| A2 | All 7 sections present | PASS/FAIL | [Sections: One-Liner, Problem Statement, Solution Approach, Success Criteria, Key Assumptions, Data & Model Strategy, Constraints & Risks] |
| A3 | No [PLACEHOLDER] tokens | PASS/FAIL | [0 placeholders found] |
| A4 | Job statement format "When/Want/So" | PASS/FAIL | [Format validated in Problem Statement section] |
| A5 | ≥3 assumptions documented | PASS/FAIL | [Assumptions found in Key Assumptions section] |
| A6 | ≥3 metrics defined | PASS/FAIL | [Metrics found in Success Criteria section] |
| A7 | ≥1 data source identified | PASS/FAIL | [Data sources listed in Data & Model Strategy] |
| A8 | Model approach ≥50 words | PASS/FAIL | [Word count in Model Approach subsection] |

---

## Manual Checks - Quality (5 criteria)

| ID | Criterion | Status | Notes |
| ---- | ----------- | -------- | ------- |
| Q1 | Assumptions have validation methods | PASS/FAIL/WAIVED | [Each assumption has method + effort] |
| Q2 | Metrics are SMART | PASS/FAIL/WAIVED | [Targets, measures, timeframes defined] |
| Q3 | Data sources concrete (named + availability %) | PASS/FAIL/WAIVED | [Sources with % readiness] |
| Q4 | Model rationale present | PASS/FAIL/WAIVED | [Why this approach fits constraints] |
| Q5 | Risk mitigations defined | PASS/FAIL/WAIVED | [Each risk has mitigation] |

---

## Manual Checks - AI-Specific (4 criteria)

| ID | Criterion | Status | Notes |
| ---- | ----------- | -------- | ------- |
| AI1 | Data readiness ≥60% | PASS/FAIL/WAIVED | [Calculated average readiness] |
| AI2 | Evaluation strategy defined | PASS/FAIL/WAIVED | [Metrics, benchmarks, human review] |
| AI3 | Safety assessment complete | PASS/FAIL/WAIVED | [Risks + mitigations] |
| AI4 | Cost viability aligned | PASS/FAIL/WAIVED | [Budget vs estimated cost] |

---

## Manual Checks - Consistency (3 criteria)

| ID | Criterion | Status | Notes |
| ---- | ----------- | -------- | ------- |
| C1 | JTBD outcomes ↔ Metrics alignment | PASS/FAIL/WAIVED | [Outcome-to-metric mapping] |
| C2 | Lean solution ↔ AI task alignment | PASS/FAIL/WAIVED | [Solution maps to AI task] |
| C3 | Constraints ↔ Model choice alignment | PASS/FAIL/WAIVED | [Latency/cost vs model] |

---

## Waivers (if applicable)

### Waiver W1: [Criterion ID] - [Criterion Name]

**Justification**: [Why this criterion cannot be met or is not applicable]
**Risk Assessment**: [What could go wrong by waiving this]
**Risk Mitigation**: [How to reduce waiver risk]
**Tracking Method**: [How to monitor this gap during implementation]
**Approved By**: [User name]
**Timestamp**: [ISO_8601_TIMESTAMP]

---

## Overall Assessment

**Score Breakdown**:

- Automated Checks: [X/8] passed
- Manual Checks - Quality: [X/5] passed
- Manual Checks - AI-Specific: [X/4] passed
- Manual Checks - Consistency: [X/3] passed
- **Total**: [X/20] ([percentage]%)

**Threshold**: ≥18/20 (90%) required for PROCEED

**Status Determination**:

- **PASS**: All 8 automated checks passed + ≥18/20 total score + no waivers
- **PASS WITH WAIVER**: All 8 automated checks passed + ≥18/20 total score + waivers documented
- **FAIL**: <18/20 total score OR automated checks failed

**Decision**:

- **PROCEED**: Ready for `/speckit.constitution` handoff
- **BLOCK**: Fix issues and re-validate OR document additional waivers

---

## User Approval

**Name**: [User name]
**Decision**: [PROCEED / BLOCK / REQUEST REVISION]
**Timestamp**: [ISO_8601_TIMESTAMP]
**Signature**: [Digital signature or explicit "APPROVED" statement]
**Notes**: [Any additional comments]
