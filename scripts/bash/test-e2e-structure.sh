#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(CDPATH="" cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(CDPATH="" cd "$SCRIPT_DIR/../.." && pwd)"
TMP_DIR="$(mktemp -d)"

cleanup() {
  rm -rf "$TMP_DIR"
}
trap cleanup EXIT

FILE_PATH="$TMP_DIR/ai_vision_canvas.md"

cat > "$FILE_PATH" <<'EOF'
# AI System Vision Canvas: Test

### 1. Job Statement (When/Want/So)
When a support agent triages tickets, I want automated routing, so I can resolve issues faster.

### 2. Job Executor
Support agent

### 3. Job Context
High-volume queue during business hours.

### 4. Desired Outcomes
- Reduce handling time
- Improve SLA compliance

### 5. Current Solution Pains
Manual triage is slow and inconsistent.

### 6. Top 3 Problems
- Manual routing
- Inconsistent tagging
- Long response time

### 7. Solution (High-Level)
Automate triage and routing with AI assistance.

### 8. Key Assumptions (Critical, Unvalidated)
Assumption A, B, C.

### 9. Validation Methods (Build-Measure-Learn)
Pilot on 10% of tickets, compare SLAs.

### 10. Key Metrics (Success Criteria)
- SLA adherence
- Time to first response
- Accuracy of routing

### 11. Cost Structure (Budget Constraints)
Budget $5k/month.

### 12. AI Task
Classify and route tickets.

### 13. Data Requirements
- Historical tickets
- Label quality

### 14. Model Approach
Lightweight classifier with prompt-based rationale.

### 15. Evaluation Strategy
Precision/recall + human review.

### 16. Safety & Risk
Misrouting risk with mitigation.

### 17. Constraints
Latency < 2s, cost cap.

### 18. Infrastructure (High-Level)
Hosted inference with queue integration.
EOF

"$REPO_ROOT/scripts/bash/validate-canvas.sh" "$FILE_PATH"
echo "STRUCTURE E2E passed"
