#!/usr/bin/env bash
# Requires: Bash 4+
# strategic-review.sh - Readiness review scaffold for strategic-review artifact.
#
# Creates .ideas/evaluation-results.md with a structured pre-launch review template.
#
# Usage:
#   ./strategic-review.sh [--force] [--help] [PROJECT_DIR]

set -euo pipefail

if ((BASH_VERSINFO[0] < 4)); then
    echo "Error: Bash 4.0 or higher is required (running: ${BASH_VERSION})." >&2
    exit 1
fi

for dep in date mkdir cat; do
    if ! command -v "$dep" >/dev/null 2>&1; then
        echo "Error: required dependency '$dep' is not available in PATH." >&2
        exit 1
    fi
done

FORCE=false
PROJECT_DIR=""

for arg in "$@"; do
    case "$arg" in
        --force) FORCE=true ;;
        --help|-h)
            echo "Usage: $(basename "$0") [--force] [--help] [PROJECT_DIR]"
            echo ""
            echo "Scaffold .ideas/evaluation-results.md for strategic launch readiness review."
            echo ""
            echo "Arguments:"
            echo "  PROJECT_DIR   Target project directory (default: current directory)"
            echo ""
            echo "Options:"
            echo "  --force       Overwrite existing evaluation-results.md"
            echo "  --help, -h    Show this help message"
            echo ""
            echo "Next steps after running:"
            echo "  1. Fill all TODO fields in .ideas/evaluation-results.md"
            echo "  2. Complete scorecard values and action items"
            echo "  3. Validate: scripts/bash/validate-strategic-review.sh .ideas/evaluation-results.md"
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
PROJECT_DIR_LOWER="${PROJECT_DIR,,}"

case "$PROJECT_DIR" in
    /|/etc|/usr|/bin|/sbin|/lib|/lib64|/boot|/proc|/sys|/dev)
        echo "Error: Refusing to use system directory as project directory: $PROJECT_DIR" >&2
        exit 1
        ;;
esac

case "$PROJECT_DIR_LOWER" in
    /mnt/c/windows|/mnt/c/windows/*|/mnt/c/program\ files|/mnt/c/program\ files/*|/mnt/c/program\ files\ \(x86\)|/mnt/c/program\ files\ \(x86\)/*|/mnt/c/programdata|/mnt/c/programdata/*|/mnt/c/users/all\ users|/mnt/c/users/all\ users/*|/c/windows|/c/windows/*|/c/program\ files|/c/program\ files/*|/c/program\ files\ \(x86\)|/c/program\ files\ \(x86\)/*|/c/programdata|/c/programdata/*|c:/windows|c:/windows/*|c:/program\ files|c:/program\ files/*|c:/program\ files\ \(x86\)|c:/program\ files\ \(x86\)/*|c:/programdata|c:/programdata/*)
        echo "Error: Refusing to use Windows system directory as project directory: $PROJECT_DIR" >&2
        exit 1
        ;;
esac

PROJECT_NAME="$(basename "$PROJECT_DIR")"
IDEAS_DIR="$PROJECT_DIR/.ideas"
TARGET="$IDEAS_DIR/evaluation-results.md"
TIMESTAMP="$(date -u +%Y-%m-%dT%H:%M:%SZ)"

if [ -L "$IDEAS_DIR" ]; then
    echo "Error: $IDEAS_DIR is a symlink. Remove it manually before proceeding." >&2
    exit 1
fi

if [ -e "$IDEAS_DIR" ] && [ ! -d "$IDEAS_DIR" ]; then
    echo "Error: $IDEAS_DIR exists but is not a directory. Remove it manually before proceeding." >&2
    exit 1
fi

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
artifact: evaluation_results
phase: strategy
schema_version: "1.0"
generated: ${TIMESTAMP}
derived_from:
  - .ideas/brainstorm-expansion.md
  - .ideas/execution-plan.md
enables: .ideas/launch-blockers.md
---

# ${PROJECT_NAME} -- Strategic Review (Pre-Launch Evaluation)

**Date:** ${TIMESTAMP}
**Overall Score:** TODO
**Band:** TODO
**Recommendation:** TODO

---

## 1. Output Quality Evaluation

TODO: Evaluate each relevant output with concrete evidence and summarize key risks.

## 2. Cross-Output Consistency

TODO: Document variance, bias patterns, and edge-case consistency gaps.

## 3. README Conversion Audit

TODO: Evaluate conversion-critical README elements and prioritize corrections.

## 4. Developer Experience Audit

TODO: Validate install, first-use flow, error quality, and help discoverability.

## 5. Security & Trust Audit

TODO: Verify secrets handling, subprocess safety, dependency posture, and attribution.

## 6. Competitive Positioning

TODO: Summarize competitor checks and positioning confidence before launch.

## 7. Launch Readiness Scorecard

| Category | Score (1-5) | Weight | Weighted |
| --- | --- | --- | --- |
| Output quality | TODO | 0.25 | TODO |
| README/docs quality | TODO | 0.20 | TODO |
| Developer experience | TODO | 0.20 | TODO |
| Security/trust | TODO | 0.15 | TODO |
| Competitive positioning | TODO | 0.10 | TODO |
| Test coverage | TODO | 0.10 | TODO |
| **TOTAL** | TODO | 1.00 | TODO |

## 8. Action Items

### Blockers (MUST fix)
1. TODO
2. TODO

### Improvements (SHOULD fix)
1. TODO
2. TODO

### Nice-to-Have (CAN fix)
1. TODO
2. TODO

## Appendix A - Evidence Log

TODO: Add concrete references (files, commands, outputs) supporting each score.

## Appendix B - Notes

TODO: Add assumptions, open questions, and deferred decisions.
EOF2

echo "Created: $TARGET"
echo ""
echo "Next steps:"
echo "  1. Fill all TODO fields"
echo "  2. Complete scorecard values and action-item sections"
echo "  3. Validate: scripts/bash/validate-strategic-review.sh $TARGET"
