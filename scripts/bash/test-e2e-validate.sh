#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(CDPATH="" cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(CDPATH="" cd "$SCRIPT_DIR/../.." && pwd)"
TMP_DIR="$(mktemp -d)"

cleanup() {
  rm -rf "$TMP_DIR"
}
trap cleanup EXIT

FILE_PATH="$TMP_DIR/vision_brief.md"

cat > "$FILE_PATH" <<'EOF'
---
artifact: vision_brief
phase: structure
generated: 2026-01-13T00:00:00Z
derived_from: .spec-kit/ai_vision_canvas.md
gate_g0_status: pending
---

# Vision Brief: Ticket Triage Assistant

**Generated**: 2026-01-13T00:00:00Z
**Derived From**: AI Vision Canvas (18 components)

## One-Liner
AI-assisted ticket routing to reduce support response times.

**Canvas References**: C7 (Solution), C12 (AI Task)

## Problem Statement
**Job-to-be-Done**: When a support agent triages tickets, I want automated routing, so I can resolve issues faster.
**Context**: High-volume support queue.
**Current Solution Pains**: Manual triage is slow and inconsistent.

**Canvas References**: C1 (Job Statement), C3 (Context), C5 (Pains)

## Solution Approach
**High-Level Design**: Automate triage and routing aligned with AI task classification.
**AI Approach**: Use a lightweight classifier with retrieval prompts and guardrails.
**How It Works**: Ingest ticket, extract intent, classify, route, and surface rationale.

**Canvas References**: C7 (Solution), C12 (AI Task), C14 (Model Approach), C15 (Evaluation)

## Success Criteria
1. Reduce time to first response by 30% within 60 days.
2. Achieve routing accuracy above 85% on a held-out set.
3. Improve SLA compliance to 95% in pilot queues.

**Canvas References**: C10 (Key Metrics)

## Key Assumptions
| Assumption | Validation Method | Risk If Wrong | Tracking |
|------------|-------------------|---------------|----------|
| Agents will adopt AI routing | Pilot + survey | Low adoption | Weekly adoption rate |
| Data labels are reliable | Audit 200 samples | Misrouting | Label quality score |
| Latency will stay <2s | Load test | SLA breach | P95 latency |

**Canvas References**: C8 (Assumptions), C9 (Validation Methods)

## Data & Model Strategy
**Data Requirements**: Historical tickets and metadata.
- Zendesk export (80% ready)
- Internal ticket logs (70% ready)

**Model Approach**: We will start with a compact classifier fine-tuned on historical tickets and clear label guidelines. The system will combine supervised learning with prompt-based guards for edge cases, backed by retrieval of prior resolved tickets. This balances accuracy, latency, and cost while enabling iterative improvement from human feedback loops and periodic evaluation against a stable benchmark set.

**Evaluation**: Precision/recall on holdout set + 100 human reviews.

**Canvas References**: C13 (Data Requirements), C14 (Model Approach), C15 (Evaluation)

## Constraints & Risks
**Budget Constraints**: $5k/month.
**Technical Constraints**: Latency <2s, context limits for long tickets.
**Safety Risks**: Misrouting harms customers; mitigation includes human override.
**Compliance**: GDPR/PII handling.

**Canvas References**: C11 (Cost), C17 (Constraints), C16 (Safety & Risk)

---

**Approval**: _[Awaiting Gate G0 validation]_
EOF

"$REPO_ROOT/scripts/bash/validate-g0.sh" "$FILE_PATH"
echo "VALIDATE E2E passed"
