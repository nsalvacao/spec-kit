# Nexo Spec Kit — Product Positioning

> **One-liner:** The structured AI development toolkit that turns ideas into
> executable specifications — with Phase 0 ideation, enterprise controls, and
> multi-agent orchestration built in.

## Problem Statement

Modern software teams using AI coding assistants face a structural gap: AI
agents are excellent at *implementing* but poor at *deciding what to build*.
Without a structured front-end discovery phase, teams accumulate poorly-scoped
features, duplicated context, and brittle handoffs between AI agents and human
reviewers.

Existing specification toolkits focus on the *how* (spec templates, plan
documents) but skip the *why* (ideation, strategic selection, scope validation).
This forces teams to bolt on ad-hoc ideation steps or skip them entirely.

## Target Users

| Segment | Description | Primary Pain |
| ------- | ----------- | ------------ |
| **AI-native engineering teams** | Teams using 2+ AI coding agents simultaneously | Agent context fragmentation, duplicated effort |
| **Product + Engineering hybrids** | Teams where PMs co-author specifications | Tooling that handles only dev-facing workflows |
| **Enterprise software shops** | Organizations with compliance, provenance, and audit requirements | No structured record-keeping for AI decisions |
| **Open-source maintainers** | Projects adopting AI-assisted contribution workflows | Missing governance layer for AI PRs |

## Elevator Pitch

**Nexo Spec Kit** is an independent toolkit and CLI for teams who build
software with AI agents. It implements a complete Spec-Driven Development (SDD)
pipeline that starts *before* any code is written:

1. **Phase 0 — Ideate**: Structured AI ideation using SCAMPER, Blue Ocean, and
   JTBD frameworks to discover what to build.
2. **Phase 1 — Specify**: Author executable specifications that constrain agents
   to the right scope.
3. **Phase 2 — Plan and implement**: Generate traceable implementation plans and
   delegate execution to AI agents.
4. **Phase 3 — Validate**: Automated scope gates, contract validation, and
   handoff metadata ensure each output is auditable.

Unlike upstream `github/spec-kit`, Nexo Spec Kit ships Phase 0 as a first-class
workflow, adds enterprise compliance controls, and integrates 17+ AI coding
agents out of the box.

## Differentiation Matrix

| Capability | Upstream `github/spec-kit` | **Nexo Spec Kit** |
| ---------- | -------------------------- | ----------------- |
| Phase 0 AI ideation | ❌ Not included | ✅ Full IDEATE → SELECT → STRUCTURE → VALIDATE |
| Multi-agent bootstrapping | Partial (Claude, Copilot) | ✅ 17+ agents (Claude, Gemini, Copilot, Cursor, Qwen, opencode, Codex, Windsurf, Kilo Code, Auggie, Roo Code, CodeBuddy, Qoder, Amazon Q, Amp, SHAI, IBM Bob) |
| Scope gate contracts | ❌ | ✅ Programmatic scope-gate validation |
| Handoff metadata schema | ❌ | ✅ Structured handoff with provenance tracking |
| Orchestration contract | ❌ | ✅ Typed orchestration contract with strict/non-strict modes |
| Extension system | ❌ | ✅ Built-in extension management (`specify extensions`) |
| Enterprise compliance guard | ❌ | ✅ Compliance checker, legal markers, trademark policy |
| Release deploy pipeline | ❌ | ✅ VM deploy + Google Drive backup workflows |
| Upstream compatibility | N/A | ✅ Opt-in upstream template layer |
| MIT license | ✅ | ✅ Preserved with attribution |

## Value Pillars

### 1. Structured Discovery (Phase 0)

AI agents work best when given clear, bounded objectives. Phase 0 transforms
vague ideas into ranked, scoped feature candidates before a single spec is
written. Commands: `/speckit.ideate`, `/speckit.select`, `/speckit.structure`,
`/speckit.validate`.

### 2. Executable Specifications

Specifications are not documents — they are contracts between human intent and
AI execution. The SDD workflow (`/speckit.constitution`, `/speckit.specify`,
`/speckit.plan`, `/speckit.tasks`, `/speckit.implement`, `/speckit.amend`)
produces artifacts that agents can directly consume.

### 3. Enterprise-Grade Governance

Every AI decision is traceable. Handoff metadata, scope gate validations,
orchestration contracts, and provenance playbooks create an auditable trail
from idea to shipped code.

### 4. Broad Agent Integration Surface

Teams choose their AI tools. Nexo Spec Kit generates the right configuration
for each agent rather than locking teams into a single provider. New agents are
added via a documented, convention-driven integration pattern (see `AGENTS.md`).

## Promise and Non-Goals

### Promise

- Every project bootstrapped with `specify init` has a documented Phase 0
  artifact and a spec-ready directory structure within minutes.
- Every AI agent interaction is scoped, traceable, and reproducible.
- Enterprise teams can adopt Nexo Spec Kit without sacrificing compliance or
  audit requirements.

### Non-Goals

- **Not a code generator**: Nexo Spec Kit orchestrates AI agents; it does not
  generate application code itself.
- **Not a CI/CD system**: Release and deploy workflows are lightweight helpers,
  not a replacement for a full platform engineering stack.
- **Not a managed SaaS**: This is an open-source CLI and template toolkit.
  No hosted infrastructure is required or provided.
- **Not a GitHub product**: This toolkit is not affiliated with, endorsed by,
  or supported by GitHub. See `docs/trademarks.md`.

## Compatibility Statement

Nexo Spec Kit is **upstream-compatible** with `github/spec-kit`:

- `specify init` pulls templates from `nsalvacao/spec-kit` by default.
- Set `SPECIFY_TEMPLATE_REPO=github/spec-kit` or pass
  `--template-repo github/spec-kit` to use upstream templates.
- All extensions are additive and isolated to templates, scripts, and
  documented overrides. No upstream behaviour is removed or replaced.
- Upstream intake is governed by the 7-step workflow in `AGENTS.md`, with
  provenance tracking via `git cherry-pick -x`.

For the compatibility policy detail, see `docs/compatibility.md`.
For upstream sync procedures, see `docs/upstream-sync.md`.

## Related Documents

- [ADR: Positioning Model](adr-positioning-model.md) — Decision record for the
  chosen strategic positioning.
- [Compatibility Policy](compatibility.md) — Upstream compatibility guarantees.
- [Upstream Sync](upstream-sync.md) — Intake workflow.
- [Legal Compliance](legal-compliance.md) — Trademark, license, and compliance
  policy.
- [Trademarks](trademarks.md) — Attribution-only trademark usage.
