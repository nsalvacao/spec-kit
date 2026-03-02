#!/usr/bin/env bash
# Requires: Bash 4+
# brainstorm.sh — Strategy pre-phase scaffold for strategic brainstorm artifact.
#
# Creates .ideas/brainstorm-expansion.md with the native structured framework.
#
# Usage:
#   ./brainstorm.sh [--force] [--help] [PROJECT_DIR]

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
            echo "Scaffold .ideas/brainstorm-expansion.md for strategic brainstorm."
            echo ""
            echo "Arguments:"
            echo "  PROJECT_DIR   Target project directory (default: current directory)"
            echo ""
            echo "Options:"
            echo "  --force       Overwrite existing brainstorm-expansion.md"
            echo "  --help, -h    Show this help message"
            echo ""
            echo "Next steps after running:"
            echo "  1. Fill all TODO fields in .ideas/brainstorm-expansion.md"
            echo "  2. Complete all 11 required sections"
            echo "  3. Keep at least 20 divergent ideas and 5 risks"
            echo "  4. Validate: scripts/bash/validate-brainstorm.sh .ideas/brainstorm-expansion.md"
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
TARGET="$IDEAS_DIR/brainstorm-expansion.md"
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
artifact: brainstorm_expansion
phase: strategy
schema_version: "1.0"
generated: ${TIMESTAMP}
derived_from: null
enables: .spec-kit/ideas_backlog.md
---

# ${PROJECT_NAME} — Strategic Brainstorm

**Date:** ${TIMESTAMP}
**Objective:** TODO: Define the strategic objective in one line.

---

## 1. What Is the REAL Asset?

TODO: Explain code vs concept vs moat with one key insight.

## 2. SCAMPER Analysis

### S — Substitute
TODO: Add substitutions with concrete opportunities.

### C — Combine
TODO: Add combinations that create differentiated value.

### A — Adapt
TODO: Add adjacent domains/personas worth adapting to.

### M — Modify / Magnify
TODO: Add 10x scope/depth/intelligence scenarios.

### P — Put to Other Uses
TODO: Add non-obvious applications.

### E — Eliminate
TODO: Add constraints/dependencies to remove.

### R — Reverse / Rearrange
TODO: Add inversion/reordering opportunities.

## 3. Divergent Ideation — 20 Wild Ideas

1. TODO: Idea 01
2. TODO: Idea 02
3. TODO: Idea 03
4. TODO: Idea 04
5. TODO: Idea 05
6. TODO: Idea 06
7. TODO: Idea 07
8. TODO: Idea 08
9. TODO: Idea 09
10. TODO: Idea 10
11. TODO: Idea 11
12. TODO: Idea 12
13. TODO: Idea 13
14. TODO: Idea 14
15. TODO: Idea 15
16. TODO: Idea 16
17. TODO: Idea 17
18. TODO: Idea 18
19. TODO: Idea 19
20. TODO: Idea 20

## 4. Convergent Analysis — Tier Ranking

### Tier S — Transformative (100k+ potential)

#### S1: TODO: Transformative initiative 1
TODO: What, why huge, path, comparable, risk, effort.

### Tier A — High Impact (10k-50k potential)

#### A1: TODO: High-impact initiative 1
TODO: What, why huge, path, comparable, risk, effort.

### Tier B — Strong (1k-10k potential)

TODO: Add at least 3 strong near-term options.

## 5. Blue Ocean Strategy

### Current Market (Red Ocean)
TODO: Add competitor table with real weaknesses.

### Blue Ocean Opportunity
TODO: Add strategic canvas and positioning statement.

## 6. TAM/SAM/SOM

TODO: Add market sizing table and key insight.

## 7. Jobs-to-be-Done

TODO: Add 3-4 persona job statements (functional/emotional/social).

## 8. Flywheel

TODO: Add ASCII flywheel, push point, and friction points.

## 9. One-Line Pitches

1. TODO: For developers
2. TODO: For enterprises
3. TODO: For AI companies
4. TODO: For investors
5. TODO: For CLI/tool authors

## 10. Honest Weaknesses & Risks

| Weakness | Severity | Probability | Mitigation |
| --- | --- | --- | --- |
| TODO: Risk 1 | High | Medium | TODO |
| TODO: Risk 2 | Medium | Medium | TODO |
| TODO: Risk 3 | Medium | Low | TODO |
| TODO: Risk 4 | High | High | TODO |
| TODO: Risk 5 | Low | Medium | TODO |

## 11. Monday Morning Actions

1. TODO: Highest-leverage action 1
2. TODO: Highest-leverage action 2
3. TODO: Highest-leverage action 3
4. TODO: Highest-leverage action 4
5. TODO: Highest-leverage action 5
EOF2

echo "Created: $TARGET"
echo ""
echo "Next steps:"
echo "  1. Fill all TODO fields"
echo "  2. Keep at least 20 divergent ideas, 3+ S/A entries, and 5+ risks"
echo "  3. Validate: scripts/bash/validate-brainstorm.sh $TARGET"
