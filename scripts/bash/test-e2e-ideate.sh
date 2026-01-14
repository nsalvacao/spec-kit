#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(CDPATH="" cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(CDPATH="" cd "$SCRIPT_DIR/../.." && pwd)"
TMP_DIR="$(mktemp -d)"

cleanup() {
  rm -rf "$TMP_DIR"
}
trap cleanup EXIT

FILE_PATH="$TMP_DIR/ideas_backlog.md"

cat > "$FILE_PATH" <<'EOF'
# Ideas Backlog: Test

### Idea S1
**Text**: Seed idea one.
**Tag**: SEED
**Generated**: 2026-01-13T00:00:00Z

---

### Idea S2
**Text**: Seed idea two.
**Tag**: SEED
**Generated**: 2026-01-13T00:00:00Z

---

### Idea SC1-Substitute
**Text**: Substitute variation.
**Tag**: SCAMPER-Substitute
**Provenance**: Derived from Seed Idea S1
**Generated**: 2026-01-13T00:00:00Z

---

### Idea SC1-Combine
**Text**: Combine variation.
**Tag**: SCAMPER-Combine
**Provenance**: Derived from Seed Idea S1
**Generated**: 2026-01-13T00:00:00Z

---

### Idea SC1-Adapt
**Text**: Adapt variation.
**Tag**: SCAMPER-Adapt
**Provenance**: Derived from Seed Idea S1
**Generated**: 2026-01-13T00:00:00Z

---

### Idea SC1-Modify
**Text**: Modify variation.
**Tag**: SCAMPER-Modify
**Provenance**: Derived from Seed Idea S1
**Generated**: 2026-01-13T00:00:00Z

---

### Idea SC1-Put-to-another-use
**Text**: Put-to-another-use variation.
**Tag**: SCAMPER-Put-to-another-use
**Provenance**: Derived from Seed Idea S1
**Generated**: 2026-01-13T00:00:00Z

---

### Idea SC1-Eliminate
**Text**: Eliminate variation.
**Tag**: SCAMPER-Eliminate
**Provenance**: Derived from Seed Idea S1
**Generated**: 2026-01-13T00:00:00Z

---

### Idea SC1-Reverse
**Text**: Reverse variation.
**Tag**: SCAMPER-Reverse
**Provenance**: Derived from Seed Idea S1
**Generated**: 2026-01-13T00:00:00Z

---

### Idea HMW1
**Text**: HMW data idea.
**Tag**: HMW-Data
**Provenance**: Generated from question "How might we improve data quality?"
**Generated**: 2026-01-13T00:00:00Z

---

### Idea HMW2
**Text**: HMW model idea.
**Tag**: HMW-Model
**Provenance**: Generated from question "How might we reduce hallucinations?"
**Generated**: 2026-01-13T00:00:00Z

---

### Idea HMW3
**Text**: HMW safety idea.
**Tag**: HMW-Safety
**Provenance**: Generated from question "How might we mitigate safety risks?"
**Generated**: 2026-01-13T00:00:00Z

---

### Idea HMW4
**Text**: HMW cost idea.
**Tag**: HMW-Cost
**Provenance**: Generated from question "How might we control costs?"
**Generated**: 2026-01-13T00:00:00Z

---

### Idea HMW5
**Text**: HMW UX idea.
**Tag**: HMW-UX
**Provenance**: Generated from question "How might we improve UX?"
**Generated**: 2026-01-13T00:00:00Z
EOF

"$REPO_ROOT/scripts/bash/validate-scamper.sh" "$FILE_PATH"
echo "IDEATE E2E passed"
