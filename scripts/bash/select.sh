#!/usr/bin/env bash
# Requires: Bash 4+
# select.sh — Phase 0 SELECT: scaffold idea_selection.md
#
# Creates .spec-kit/idea_selection.md from the standard AI-RICE template.
# Run this after completing Phase 0 IDEATE to score and select ideas.
#
# Usage:
#   ./select.sh [--force] [--help] [PROJECT_DIR]
#
# Arguments:
#   PROJECT_DIR   Target project directory (default: current directory)
#
# Options:
#   --force       Overwrite existing idea_selection.md
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
            echo "Scaffold .spec-kit/idea_selection.md for Phase 0 selection (AI-RICE scoring)."
            echo ""
            echo "Arguments:"
            echo "  PROJECT_DIR   Target project directory (default: current directory)"
            echo ""
            echo "Options:"
            echo "  --force       Overwrite existing idea_selection.md"
            echo "  --help, -h    Show this help message"
            echo ""
            echo "Prerequisites:"
            echo "  - .spec-kit/ideas_backlog.md must exist (run ideate.sh first)"
            echo "  - ideas_backlog.md must pass validate-scamper.sh"
            echo ""
            echo "Next steps after running:"
            echo "  1. Open .spec-kit/idea_selection.md and fill in AI-RICE scores"
            echo "  2. AI-RICE formula: (Reach * Impact * Confidence * Data_Readiness) / (Effort * Risk)"
            echo "  3. Normalise scores: best idea = 100, others relative"
            echo "  4. Run: validate-airice.sh .spec-kit/idea_selection.md"
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

SPEC_KIT_DIR="$PROJECT_DIR/.spec-kit"
TARGET="$SPEC_KIT_DIR/idea_selection.md"
TIMESTAMP="$(date -u +%Y-%m-%dT%H:%M:%SZ)"

# Refuse to overwrite symlinks
if [ -L "$TARGET" ]; then
    echo "Error: $TARGET is a symlink. Remove it manually before proceeding." >&2
    exit 1
fi

# Check idempotency
if [ -f "$TARGET" ] && [ "$FORCE" = "false" ]; then
    echo "Error: $TARGET already exists. Use --force to overwrite." >&2
    exit 1
fi

# Create .spec-kit directory
mkdir -p "$SPEC_KIT_DIR"

# Write scaffolded idea_selection.md
cat > "$TARGET" <<EOF
---
artifact: idea_selection
phase: select
schema_version: "1.0"
generated: ${TIMESTAMP}
ideas_evaluated: 0
selected_idea_id: TBD
derived_from: .spec-kit/ideas_backlog.md
enables: .spec-kit/ai_vision_canvas.md
---

# Idea Selection Report

**Generated**: ${TIMESTAMP}
**Ideas Evaluated**: 0
**Source Backlog**: [ideas_backlog.md](.spec-kit/ideas_backlog.md)

<!--
Guidance:

- AI-RICE is based on RICE (Reach, Impact, Confidence, Effort).
- AI-RICE adds Data_Readiness and Risk.
- Idea IDs in the table MUST link to the corresponding heading anchor in ideas_backlog.md.
- Input dimension guidelines:
  - Reach: number of users/sessions impacted per quarter. Examples: 100 (niche), 1000 (small), 10000 (medium).
  - Impact: 0.25 (minimal), 0.5 (low), 1.0 (normal), 2.0 (high), 3.0 (massive).
  - Confidence: 0-100% (enter as integer percentage, e.g. 70%).
  - Data_Readiness: 0-100% (enter as integer percentage).
  - Effort: person-weeks. Examples: 1 (days), 4 (1 month), 12 (1 quarter).
  - Risk: 1-10 (higher = riskier). 1-3 low, 4-6 medium, 7-10 high.
- Norm_Score = (AI-RICE_raw / session_max_raw) * 100, rounded to 1 decimal.
- Score interpretation: 70-100 = Strong; 40-69 = Viable; 0-39 = Weak.
-->

## AI-RICE Scoring Table

| Idea ID | Reach | Impact | Confidence | Data_Readiness | Effort | Risk | AI-RICE Score | Norm_Score |
| ------- | ----- | ------ | ---------- | -------------- | ------ | ---- | ------------- | ---------- |
| [S1](.spec-kit/ideas_backlog.md#idea-s1) | 0 | 1.0 | 0% | 0% | 1 | 5 | 0.0 | 0.0 |
| [S2](.spec-kit/ideas_backlog.md#idea-s2) | 0 | 1.0 | 0% | 0% | 1 | 5 | 0.0 | 0.0 |

**Formula**: (Reach \* Impact \* Confidence \* Data_Readiness) / (Effort \* Risk)

**Normalization**: Norm\_Score = (AI-RICE\_raw / session\_max\_raw) × 100

## Selected Idea

**ID**: [TBD](.spec-kit/ideas_backlog.md#idea-tbd)
**Text**: [Description of the selected idea]
**Tag**: [SEED | SCAMPER-<Lens> | HMW-<Dimension>]
**AI-RICE Score**: 0.0 (Norm: 0.0/100)

### Dimensional Breakdown

- **Reach**: 0 - [rationale]
- **Impact**: 1.0 - [rationale]
- **Confidence**: 0% - [rationale]
- **Data_Readiness**: 0% - [rationale]
- **Effort**: 1 - [rationale]
- **Risk**: 5 - [rationale]

## Selection Rationale

[Why this idea scored highest; trade-offs vs runner-ups.]

## Runner-Ups (Pivot Options)

### 2nd Place: [IDEA_ID](.spec-kit/ideas_backlog.md#idea-tbd)

- **AI-RICE Score**: 0.0
- **Why Not Selected**: [Reason]
- **Pivot Trigger**: [Condition that would make this the preferred choice]
EOF

echo "✓ Created: $TARGET"
echo ""
echo "Next steps:"
echo "  1. Open $TARGET and fill in AI-RICE scores for each idea"
echo "  2. Formula: (Reach * Impact * Confidence * Data_Readiness) / (Effort * Risk)"
echo "  3. Normalise scores relative to session maximum"
echo "  4. Validate: scripts/bash/validate-airice.sh $TARGET"
