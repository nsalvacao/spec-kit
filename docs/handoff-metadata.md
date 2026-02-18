# Handoff Metadata Protocol

Every artifact in the Phase 0 → SDD pipeline carries a standard YAML frontmatter block
that enables traceability from ideation through to implementation.

## Schema (v1.0)

```yaml
---
artifact: <artifact_type>       # machine-readable type identifier
phase: <phase_name>             # ideate | select | structure | validate | sdd
schema_version: "1.0"           # metadata schema version
generated: <ISO-8601>           # creation timestamp
derived_from: <path|null>       # path to parent artifact (null for root)
enables: <path|null>            # path to next artifact (null for leaf)
---
```

## Artifact Chain

```text
Phase 0
  ideate   → ideas_backlog         (.spec-kit/ideas_backlog.md)
               ↓ derived_from: null
  select   → idea_selection        (.spec-kit/idea_selection.md)
               ↓ derived_from: ideas_backlog.md
  structure→ ai_vision_canvas      (.spec-kit/ai_vision_canvas.md)
               ↓ derived_from: idea_selection.md
             vision_brief          (.spec-kit/vision_brief.md)
               ↓ derived_from: ai_vision_canvas.md
  validate → g0_validation_report  (.spec-kit/g0_validation_report.md)
               ↓ derived_from: vision_brief.md

SDD (Gate G0 passed)
             spec                  (.specify/spec.md)
               derived_from: g0_validation_report.md
```

## Field Reference

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `artifact` | string | ✅ | Machine-readable artifact type (no spaces, underscores) |
| `phase` | string | ✅ | Phase that produced this artifact |
| `schema_version` | string | ✅ | Always `"1.0"` for this version of the protocol |
| `generated` | ISO-8601 | ✅ | Creation timestamp (`YYYY-MM-DDTHH:MM:SSZ`) |
| `derived_from` | path \| null | ✅ | Relative path from repo root to parent artifact; `null` for `ideas_backlog` |
| `enables` | path \| null | ✅ | Relative path to the next artifact in chain; `null` for `spec` |

## Why This Matters

- **Audit trail**: Every decision can be traced back to the originating idea.
- **Tooling**: Future validators can walk the chain and detect gaps (e.g., missing `idea_selection` before `vision_brief`).
- **Human review**: Reviewers can follow `derived_from` links to understand context without searching.

## Validator Hook

The `detect-phase0.sh` utility reads `schema_version` and `derived_from` when present
in `.spec-kit/state.yaml`. A future validator (`validate-constitution.sh`) will enforce
that the chain is complete before allowing SDD to proceed.
