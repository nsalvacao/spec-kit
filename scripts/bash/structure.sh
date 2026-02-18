#!/usr/bin/env bash
# Requires: Bash 4+
# structure.sh — Phase 0 STRUCTURE: scaffold ai_vision_canvas.md
#
# Creates .spec-kit/ai_vision_canvas.md from the standard AI System Vision Canvas template.
# Run this after completing Phase 0 SELECT to structure the chosen idea.
#
# Usage:
#   ./structure.sh [--force] [--help] [PROJECT_DIR]
#
# Arguments:
#   PROJECT_DIR   Target project directory (default: current directory)
#
# Options:
#   --force       Overwrite existing ai_vision_canvas.md
#   --help, -h    Show this help message

set -euo pipefail

# Bash 4+ required
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
            echo "Scaffold .spec-kit/ai_vision_canvas.md for Phase 0 structure (AI System Vision Canvas)."
            echo ""
            echo "Arguments:"
            echo "  PROJECT_DIR   Target project directory (default: current directory)"
            echo ""
            echo "Options:"
            echo "  --force       Overwrite existing ai_vision_canvas.md"
            echo "  --help, -h    Show this help message"
            echo ""
            echo "Prerequisites:"
            echo "  - .spec-kit/idea_selection.md must exist (run select.sh first)"
            echo "  - idea_selection.md must pass validate-airice.sh"
            echo ""
            echo "Next steps after running:"
            echo "  1. Open .spec-kit/ai_vision_canvas.md and complete all 18 sections"
            echo "  2. Sections: JTBD (1-5), Lean Startup (6-11), AI-Specific (12-18)"
            echo "  3. Run: validate-canvas.sh .spec-kit/ai_vision_canvas.md"
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

# Default to current directory
if [ -z "$PROJECT_DIR" ]; then
    PROJECT_DIR="$(pwd)"
fi

# Validate project directory
if [ ! -d "$PROJECT_DIR" ]; then
    echo "Error: Project directory does not exist: $PROJECT_DIR" >&2
    exit 1
fi

# Resolve to absolute path
PROJECT_DIR="$(cd "$PROJECT_DIR" && pwd)"

# Refuse dangerous system directories
case "$PROJECT_DIR" in
    /|/etc|/usr|/bin|/sbin|/lib|/lib64|/boot|/proc|/sys|/dev)
        echo "Error: Refusing to use system directory as project directory: $PROJECT_DIR" >&2
        exit 1
        ;;
esac

PROJECT_NAME="$(basename "$PROJECT_DIR")"
SPEC_KIT_DIR="$PROJECT_DIR/.spec-kit"
TARGET="$SPEC_KIT_DIR/ai_vision_canvas.md"
TIMESTAMP="$(date -u +%Y-%m-%dT%H:%M:%SZ)"

# Refuse to overwrite symlinks
if [ -L "$TARGET" ]; then
    echo "Error: $TARGET is a symlink. Remove it manually before proceeding." >&2
    exit 1
fi

# Refuse if target path is a directory
if [ -d "$TARGET" ]; then
    echo "Error: $TARGET is a directory, not a file. Remove it manually before proceeding." >&2
    exit 1
fi

# Check idempotency
if [ -f "$TARGET" ] && [ "$FORCE" = "false" ]; then
    echo "Error: $TARGET already exists. Use --force to overwrite." >&2
    exit 1
fi

# Create .spec-kit directory
mkdir -p "$SPEC_KIT_DIR"

# Write scaffolded ai_vision_canvas.md
cat > "$TARGET" <<EOF
---
artifact: ai_vision_canvas
phase: structure
schema_version: "1.0"
generated: ${TIMESTAMP}
selected_idea_id: TBD
derived_from: .spec-kit/idea_selection.md
enables: .spec-kit/vision_brief.md
---

# AI System Vision Canvas: ${PROJECT_NAME}

**Generated**: ${TIMESTAMP}
**Selected Idea**: TBD - [Short label of selected idea]

<!--
Guidance:

- JTBD (Jobs to Be Done) frames the user's progress in context (job statement + outcomes).
- Lean Startup emphasizes hypotheses and validated learning (Build-Measure-Learn).
- AI Risk Management should cover safety, transparency, robustness, and evaluation readiness.
-->

## SECTION 1: JOBS-TO-BE-DONE (5 components)

### 1. Job Statement (When/Want/So)

**When** [situation], **I want** [motivation], **so I can** [outcome].

### 2. Job Executor

Who performs the job? (role/persona)

### 3. Job Context

Where/when does this job occur? Constraints and environment.

### 4. Desired Outcomes

List measurable functional, emotional, and social outcomes.

### 5. Current Solution Pains

What is inadequate today? Where does the current approach fail?

---

## SECTION 2: LEAN STARTUP (6 components)

### 6. Top 3 Problems

The three most critical problems to solve.

### 7. Solution (High-Level)

Describe the solution approach (no tech stack yet).

### 8. Key Assumptions (Critical, Unvalidated)

List hypotheses that must be validated.

### 9. Validation Methods (Build-Measure-Learn)

For each assumption, define how you will test and measure.

### 10. Key Metrics (Success Criteria)

Define measurable indicators of success.

### 11. Cost Structure (Budget Constraints)

Budget, time constraints, and cost drivers.

---

## SECTION 3: AI-SPECIFIC (7 components)

### 12. AI Task

What does the AI predict, classify, generate, or decide?

### 13. Data Requirements

Sources, volume, quality, labeling needs, privacy constraints.

### 14. Model Approach

Model family, prompting strategy, and rationale (high level).

### 15. Evaluation Strategy

Metrics, benchmarks, and human review plan.

### 16. Safety & Risk

Primary risks, mitigations, and trustworthiness considerations.

### 17. Constraints

Latency, cost, compliance, context limits.

### 18. Infrastructure (High-Level)

Hosting, serving infrastructure, and integration points.
EOF

echo "✓ Created: $TARGET"
echo ""
echo "Next steps:"
echo "  1. Open $TARGET and complete all 18 canvas sections"
echo "  2. SECTION 1: Jobs-to-be-Done (sections 1-5)"
echo "  3. SECTION 2: Lean Startup (sections 6-11)"
echo "  4. SECTION 3: AI-Specific (sections 12-18)"
echo "  5. Validate: scripts/bash/validate-canvas.sh $TARGET"
