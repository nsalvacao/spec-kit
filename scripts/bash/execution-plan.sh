#!/usr/bin/env bash
# Requires: Bash 4+
# execution-plan.sh - Strategy planning scaffold for execution-plan artifact.
#
# Creates .ideas/execution-plan.md with a structured strategic plan template.
#
# Usage:
#   ./execution-plan.sh [--force] [--help] [PROJECT_DIR]

set -euo pipefail

if ((BASH_VERSINFO[0] < 4)); then
    echo "Error: Bash 4.0 or higher is required (running: ${BASH_VERSION})." >&2
    exit 1
fi

FORCE=false
PROJECT_DIR=""

for arg in "$@"; do
    case "$arg" in
        --force) FORCE=true ;;
        --help|-h)
            echo "Usage: $(basename "$0") [--force] [--help] [PROJECT_DIR]"
            echo ""
            echo "Scaffold .ideas/execution-plan.md for strategic execution planning."
            echo ""
            echo "Arguments:"
            echo "  PROJECT_DIR   Target project directory (default: current directory)"
            echo ""
            echo "Options:"
            echo "  --force       Overwrite existing execution-plan.md"
            echo "  --help, -h    Show this help message"
            echo ""
            echo "Next steps after running:"
            echo "  1. Fill all TODO fields in .ideas/execution-plan.md"
            echo "  2. Complete all mandatory sections and tables"
            echo "  3. Validate: scripts/bash/validate-execution-plan.sh .ideas/execution-plan.md"
            exit 0
            ;;
        --*)
            echo "Error: Unknown option '$arg'" >&2
            echo "Run '$(basename "$0") --help' for usage." >&2
            exit 1
            ;;
        *)
            if [ -n "$PROJECT_DIR" ]; then
                echo "Error: Too many arguments. Expected at most one PROJECT_DIR." >&2
                echo "Run '$(basename "$0") --help' for usage." >&2
                exit 1
            fi
            PROJECT_DIR="$arg"
            ;;
    esac
done

if [ -z "$PROJECT_DIR" ]; then
    PROJECT_DIR="$(pwd)"
fi

if [ ! -d "$PROJECT_DIR" ]; then
    echo "Error: Project directory does not exist: $PROJECT_DIR" >&2
    exit 1
fi

PROJECT_DIR="$(cd "$PROJECT_DIR" && pwd)"

case "$PROJECT_DIR" in
    /|/etc|/usr|/bin|/sbin|/lib|/lib64|/boot|/proc|/sys|/dev)
        echo "Error: Refusing to use system directory as project directory: $PROJECT_DIR" >&2
        exit 1
        ;;
esac

PROJECT_NAME="$(basename "$PROJECT_DIR")"
IDEAS_DIR="$PROJECT_DIR/.ideas"
TARGET="$IDEAS_DIR/execution-plan.md"
TIMESTAMP="$(date -u +%Y-%m-%dT%H:%M:%SZ)"

if [ -L "$TARGET" ]; then
    echo "Error: $TARGET is a symlink. Remove it manually before proceeding." >&2
    exit 1
fi

if [ -d "$TARGET" ]; then
    echo "Error: $TARGET is a directory, not a file. Remove it manually before proceeding." >&2
    exit 1
fi

if [ -f "$TARGET" ] && [ "$FORCE" = "false" ]; then
    echo "Error: $TARGET already exists. Use --force to overwrite." >&2
    exit 1
fi

mkdir -p "$IDEAS_DIR"

cat > "$TARGET" <<EOF2
---
artifact: execution_plan
phase: strategy
schema_version: "1.0"
generated: ${TIMESTAMP}
derived_from: .ideas/brainstorm-expansion.md
enables: .ideas/evaluation-results.md
---

# ${PROJECT_NAME} - Strategic Execution Plan

**Date:** ${TIMESTAMP}
**Status:** Draft v1.0
**Objective:** TODO: Define the execution objective in one sentence.

---

## Table of Contents

1. Second-Order Thinking & Anticipation Layer
2. Polish & Improvements Before Public Exposure
3. Expected Impacts Matrix
4. Operationalized Roadmap
4b. Pre-Mortem Analysis
4c. Moat Assessment
5. Risk Register
6. Growth & Visibility Strategy
7. Contrarian Challenges
Appendices

## 1. Second-Order Thinking & Anticipation Layer

### 1.1 Second-Order Effects by Initiative

#### Initiative 1: TODO
| Order | Effect | Implication |
| --- | --- | --- |
| First | TODO | TODO |
| Second | TODO | TODO |
| Third | TODO | TODO |

**Key insight:** TODO

#### Initiative 2: TODO
| Order | Effect | Implication |
| --- | --- | --- |
| First | TODO | TODO |
| Second | TODO | TODO |
| Third | TODO | TODO |

**Key insight:** TODO

#### Initiative 3: TODO
| Order | Effect | Implication |
| --- | --- | --- |
| First | TODO | TODO |
| Second | TODO | TODO |
| Third | TODO | TODO |

**Key insight:** TODO

### 1.2 Failure Modes by Phase

| Phase | Failure mode | Probability | Mitigation |
| --- | --- | --- | --- |
| Phase 1 | TODO | TODO | TODO |
| Phase 2 | TODO | TODO | TODO |
| Phase 3 | TODO | TODO | TODO |
| Phase 4 | TODO | TODO | TODO |

### 1.3 Competitive Responses

TODO: Document likely competitor responses and counter-moves.

### 1.4 Timing Risks

TODO: Document external timing risks and hedges.

### 1.5 Dependencies & Critical Path

TODO: Add dependency map and critical path notes.

## 2. Polish & Improvements Before Public Exposure

### 2.1 Code Quality Audit Checklist

| Area | Status (PASS/PARTIAL/FAIL) | Action Needed | Priority |
| --- | --- | --- | --- |
| Tests | TODO | TODO | TODO |
| Error handling | TODO | TODO | TODO |
| Security | TODO | TODO | TODO |
| CI/CD | TODO | TODO | TODO |
| Documentation | TODO | TODO | TODO |

### 2.2 Documentation Gaps

| Document | Exists (YES/NO) | Action |
| --- | --- | --- |
| README.md | TODO | TODO |
| CONTRIBUTING.md | TODO | TODO |
| CHANGELOG.md | TODO | TODO |
| Architecture docs | TODO | TODO |
| API/CLI docs | TODO | TODO |

### 2.3 README Optimization

TODO: Evaluate first impression, value proposition, and conversion friction.

### 2.4 Demo/GIF/Video Needs

TODO: Define demo assets required pre-launch.

### 2.5 Pre-Launch Evaluation Checkpoint

TODO: Define how evaluation and advanced-evaluation will be invoked before launch.

## 3. Expected Impacts Matrix

| Item | Reach | Effort (days) | Star Impact | Revenue | Moat Contribution |
| --- | --- | --- | --- | --- | --- |
| TODO | TODO | TODO | TODO | TODO | TODO |
| TODO | TODO | TODO | TODO | TODO | TODO |
| TODO | TODO | TODO | TODO | TODO | TODO |
| TODO | TODO | TODO | TODO | TODO | TODO |

## 4. Operationalized Roadmap

### Phase 1: Foundation (TODO timeframe)

#### Track A: TODO

| # | Deliverable | Acceptance Criteria | Days | Quick Win? |
| --- | --- | --- | --- | --- |
| A1 | TODO | TODO | TODO | TODO |
| A2 | TODO | TODO | TODO | TODO |

**Exit criteria:** TODO

### Phase 2: Expansion (TODO timeframe)

#### Track B: TODO

| # | Deliverable | Acceptance Criteria | Days | Quick Win? |
| --- | --- | --- | --- | --- |
| B1 | TODO | TODO | TODO | TODO |
| B2 | TODO | TODO | TODO | TODO |

**Exit criteria:** TODO

### Phase 3: Platform (TODO timeframe)

#### Track C: TODO

| # | Deliverable | Acceptance Criteria | Days | Quick Win? |
| --- | --- | --- | --- | --- |
| C1 | TODO | TODO | TODO | TODO |
| C2 | TODO | TODO | TODO | TODO |

**Exit criteria:** TODO

### Phase 4: Scale (TODO timeframe)

#### Track D: TODO

| # | Deliverable | Acceptance Criteria | Days | Quick Win? |
| --- | --- | --- | --- | --- |
| D1 | TODO | TODO | TODO | TODO |
| D2 | TODO | TODO | TODO | TODO |

**Exit criteria:** TODO

## 4b. Pre-Mortem Analysis

| # | Cause of Death | Category | Probability | Prevention |
| --- | --- | --- | --- | --- |
| 1 | TODO | Technical | TODO | TODO |
| 2 | TODO | Market | TODO | TODO |
| 3 | TODO | Execution | TODO | TODO |
| 4 | TODO | External | TODO | TODO |
| 5 | TODO | Community | TODO | TODO |
| 6 | TODO | Technical | TODO | TODO |
| 7 | TODO | Market | TODO | TODO |
| 8 | TODO | Execution | TODO | TODO |

## 4c. Moat Assessment

| Moat Type | Current | Buildable? | How | Timeline |
| --- | --- | --- | --- | --- |
| Network Effects | TODO | TODO | TODO | TODO |
| Switching Costs | TODO | TODO | TODO | TODO |
| Brand / Trust | TODO | TODO | TODO | TODO |
| Cost Advantage | TODO | TODO | TODO | TODO |

## 5. Risk Register

| # | Risk | Prob. | Impact | Mitigation |
| --- | --- | --- | --- | --- |
| 1 | TODO | TODO | TODO | TODO |
| 2 | TODO | TODO | TODO | TODO |
| 3 | TODO | TODO | TODO | TODO |
| 4 | TODO | TODO | TODO | TODO |
| 5 | TODO | TODO | TODO | TODO |
| 6 | TODO | TODO | TODO | TODO |
| 7 | TODO | TODO | TODO | TODO |
| 8 | TODO | TODO | TODO | TODO |
| 9 | TODO | TODO | TODO | TODO |
| 10 | TODO | TODO | TODO | TODO |

## 6. Growth & Visibility Strategy

### 6.1 Launch Channels

| Channel | Audience size | Timing | Expected impact | Content type |
| --- | --- | --- | --- | --- |
| TODO | TODO | TODO | TODO | TODO |
| TODO | TODO | TODO | TODO | TODO |
| TODO | TODO | TODO | TODO | TODO |

### 6.2 Content Strategy

| Week | Content piece | Channel | Purpose |
| --- | --- | --- | --- |
| 1 | TODO | TODO | TODO |
| 2 | TODO | TODO | TODO |
| 3 | TODO | TODO | TODO |
| 4 | TODO | TODO | TODO |

### 6.3 Community Building

| Mechanism | When | Why |
| --- | --- | --- |
| TODO | TODO | TODO |
| TODO | TODO | TODO |
| TODO | TODO | TODO |

### 6.4 Partnership Opportunities

| Partner type | Targets | Pitch (one line) | Timing |
| --- | --- | --- | --- |
| TODO | TODO | TODO | TODO |
| TODO | TODO | TODO | TODO |

### 6.5 HN Title A/B Testing

1. TODO: Technical angle
2. TODO: Problem-first angle
3. TODO: Analogy angle

### 6.6 Star Growth Model

| Milestone | Target date | Strategy |
| --- | --- | --- |
| TODO | TODO | TODO |
| TODO | TODO | TODO |
| TODO | TODO | TODO |

## 7. Contrarian Challenges

| Assumption | Contrarian View | Prob. Wrong | Hedge |
| --- | --- | --- | --- |
| TODO | TODO | TODO | TODO |
| TODO | TODO | TODO | TODO |
| TODO | TODO | TODO | TODO |
| TODO | TODO | TODO | TODO |
| TODO | TODO | TODO | TODO |

## Appendices

### A. Immediate Action Items (This Week)

1. TODO
2. TODO
3. TODO
4. TODO
5. TODO

### B. Key Files Reference

TODO: List key files and why they matter for the plan.

### C. Quantitative Analysis

TODO: Include quantified assumptions (cost, effort, impact, throughput, risk).
EOF2

echo "Created: $TARGET"
echo ""
echo "Next steps:"
echo "  1. Fill all TODO fields"
echo "  2. Complete all required sections with evidence-backed content"
echo "  3. Validate: scripts/bash/validate-execution-plan.sh $TARGET"
