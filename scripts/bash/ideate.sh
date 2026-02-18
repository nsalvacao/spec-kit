#!/usr/bin/env bash
# Requires: Bash 4+
# ideate.sh — Phase 0 IDEATE: scaffold ideas_backlog.md
#
# Creates .spec-kit/ideas_backlog.md from the standard SCAMPER + HMW template.
# Run this at the start of Phase 0 to begin the ideation process.
#
# Usage:
#   ./ideate.sh [--force] [--help] [PROJECT_DIR]
#
# Arguments:
#   PROJECT_DIR   Target project directory (default: current directory)
#
# Options:
#   --force       Overwrite existing ideas_backlog.md
#   --help, -h    Show this help message

set -euo pipefail

FORCE=false
PROJECT_DIR=""

for arg in "$@"; do
    case "$arg" in
        --force) FORCE=true ;;
        --help|-h)
            echo "Usage: $(basename "$0") [--force] [--help] [PROJECT_DIR]"
            echo ""
            echo "Scaffold .spec-kit/ideas_backlog.md for Phase 0 ideation."
            echo ""
            echo "Arguments:"
            echo "  PROJECT_DIR   Target project directory (default: current directory)"
            echo ""
            echo "Options:"
            echo "  --force       Overwrite existing ideas_backlog.md"
            echo "  --help, -h    Show this help message"
            echo ""
            echo "Next steps after running:"
            echo "  1. Open .spec-kit/ideas_backlog.md and add 2-5 seed ideas"
            echo "  2. Generate SCAMPER variations (7 per seed idea)"
            echo "  3. Add HMW questions (5+ across Data/Model/Safety/Cost/UX)"
            echo "  4. Run: validate-scamper.sh .spec-kit/ideas_backlog.md"
            exit 0
            ;;
        --*)
            echo "Error: Unknown option '$arg'" >&2
            echo "Run '$(basename "$0") --help' for usage." >&2
            exit 1
            ;;
        *)
            if [ -n "$PROJECT_DIR" ]; then
                echo "Error: Unexpected argument '$arg'" >&2
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
PROJECT_NAME="$(basename "$PROJECT_DIR")"
SPEC_KIT_DIR="$PROJECT_DIR/.spec-kit"
TARGET="$SPEC_KIT_DIR/ideas_backlog.md"
TIMESTAMP="$(date -u +%Y-%m-%dT%H:%M:%SZ)"

# Check idempotency
if [ -f "$TARGET" ] && [ "$FORCE" = "false" ]; then
    echo "Error: $TARGET already exists. Use --force to overwrite." >&2
    exit 1
fi

# Create .spec-kit directory
mkdir -p "$SPEC_KIT_DIR"

# Write scaffolded ideas_backlog.md
cat > "$TARGET" <<EOF
---
artifact: ideas_backlog
phase: ideate
schema_version: "1.0"
generated: ${TIMESTAMP}
seed_count: 2
total_count: 2
derived_from: null
enables: .spec-kit/idea_selection.md
---

# Ideas Backlog: ${PROJECT_NAME}

**Generated**: ${TIMESTAMP}
**Seed Ideas**: 2
**Total Ideas**: 2

<!--
Guidance:

- SCAMPER uses seven lenses: Substitute, Combine, Adapt, Modify, Put to another use, Eliminate, Reverse.
- Each seed idea MUST produce one variation per lens (7 total).
- HMW (How Might We) questions should open the problem space; create 5+ across Data/Model/Safety/Cost/UX.
- Tags MUST use the format below to enable validators.
-->

## Seed Ideas (User-Provided)

<!-- Add 2-5 seed ideas. Use Tag: SEED only. -->

### Idea S1

**Text**: [1-3 sentence description of your first seed idea]
**Tag**: SEED
**Generated**: ${TIMESTAMP}

---

### Idea S2

**Text**: [1-3 sentence description of your second seed idea]
**Tag**: SEED
**Generated**: ${TIMESTAMP}

---

## SCAMPER Variations

<!--
Tag format: SCAMPER-<Lens>
Lens values (exact):

- Substitute
- Combine
- Adapt
- Modify
- Put-to-another-use
- Eliminate
- Reverse
Each variation MUST include Provenance linking to the originating seed idea.
-->

### Idea SC1-Substitute

**Text**: [How would you substitute a core component of S1?]
**Tag**: SCAMPER-Substitute
**Provenance**: Derived from Seed Idea S1
**Generated**: ${TIMESTAMP}

---

### Idea SC1-Combine

**Text**: [What could you combine with S1 to enhance it?]
**Tag**: SCAMPER-Combine
**Provenance**: Derived from Seed Idea S1
**Generated**: ${TIMESTAMP}

---

### Idea SC1-Adapt

**Text**: [How would you adapt S1 from another domain?]
**Tag**: SCAMPER-Adapt
**Provenance**: Derived from Seed Idea S1
**Generated**: ${TIMESTAMP}

---

### Idea SC1-Modify

**Text**: [What would you modify, magnify, or minify in S1?]
**Tag**: SCAMPER-Modify
**Provenance**: Derived from Seed Idea S1
**Generated**: ${TIMESTAMP}

---

### Idea SC1-Put-to-another-use

**Text**: [What other use could S1 serve?]
**Tag**: SCAMPER-Put-to-another-use
**Provenance**: Derived from Seed Idea S1
**Generated**: ${TIMESTAMP}

---

### Idea SC1-Eliminate

**Text**: [What could you eliminate from S1 to simplify it?]
**Tag**: SCAMPER-Eliminate
**Provenance**: Derived from Seed Idea S1
**Generated**: ${TIMESTAMP}

---

### Idea SC1-Reverse

**Text**: [What would happen if you reversed or rearranged S1?]
**Tag**: SCAMPER-Reverse
**Provenance**: Derived from Seed Idea S1
**Generated**: ${TIMESTAMP}

---

## HMW Questions (How Might We)

<!--
Generate 5+ HMW questions across these dimensions:
Data, Model, Safety, Cost, UX
Tag format: HMW-<Dimension>
-->

### Idea HMW1

**Text**: [HMW question about data quality or availability]
**Tag**: HMW-Data
**Provenance**: Generated from question "How might we improve data quality?"
**Generated**: ${TIMESTAMP}

---

### Idea HMW2

**Text**: [HMW question about model performance or accuracy]
**Tag**: HMW-Model
**Provenance**: Generated from question "How might we reduce hallucinations?"
**Generated**: ${TIMESTAMP}

---

### Idea HMW3

**Text**: [HMW question about safety or risk mitigation]
**Tag**: HMW-Safety
**Provenance**: Generated from question "How might we mitigate safety risks?"
**Generated**: ${TIMESTAMP}

---

### Idea HMW4

**Text**: [HMW question about cost or resource constraints]
**Tag**: HMW-Cost
**Provenance**: Generated from question "How might we control costs?"
**Generated**: ${TIMESTAMP}

---

### Idea HMW5

**Text**: [HMW question about user experience or adoption]
**Tag**: HMW-UX
**Provenance**: Generated from question "How might we improve UX?"
**Generated**: ${TIMESTAMP}

---
EOF

echo "✓ Created: $TARGET"
echo ""
echo "Next steps:"
echo "  1. Open $TARGET and fill in seed ideas and variations"
echo "  2. Generate 7 SCAMPER variations per seed idea"
echo "  3. Add 5+ HMW questions across Data/Model/Safety/Cost/UX"
echo "  4. Validate: scripts/bash/validate-scamper.sh $TARGET"
