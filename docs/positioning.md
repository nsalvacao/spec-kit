# Nexo Spec Kit — Product Positioning

> **One-liner:** The structured AI development toolkit that turns ideas into
> executable specifications — with Phase 0 ideation, enterprise controls, and
> programmatic governance built in.

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
software with AI agents. It extends Spec-Driven Development with a Phase 0
discovery layer that runs *before* any spec is written:

1. **Phase 0 — Ideate**: Structured AI ideation using SCAMPER + HMW to generate
   an ideas backlog. Select a winner with AI-RICE scoring. Complete the
   Integrated AI Vision Canvas and vision brief. Gate G0 validation.
2. **SDD Core — Specify**: Author executable specifications that constrain agents
   to the right scope (`/speckit.constitution`, `/speckit.specify`,
   `/speckit.clarify`).
3. **SDD Core — Plan and implement**: Generate traceable implementation plans
   and delegate execution to AI agents (`/speckit.plan`, `/speckit.tasks`,
   `/speckit.implement`, `/speckit.amend`).
4. **Enterprise layer**: Scope gate contracts, handoff metadata, orchestration
   contracts, and a compliance checker create an auditable trail from idea to
   shipped code.

Nexo Spec Kit integrates with **18 AI coding agents** (Claude Code, Gemini CLI,
GitHub Copilot, Cursor, Qwen Code, opencode, Codex CLI, Windsurf, Kilo Code,
Auggie CLI, Roo Code, CodeBuddy, Qoder CLI, Amazon Q Developer CLI, Amp, SHAI,
Antigravity, IBM Bob) and remains upstream-compatible with `github/spec-kit`.

## Differentiation Matrix

The following table compares Nexo Spec Kit with the upstream
`github/spec-kit` project based on capabilities verifiable in each
repository's source code and documentation at the time of writing.

| Capability | Upstream `github/spec-kit` | **Nexo Spec Kit** |
| ---------- | -------------------------- | ----------------- |
| Phase 0 AI ideation (IDEATE → SELECT → STRUCTURE → VALIDATE) | ❌ | ✅ Full workflow with state checks and G0 gate |
| `/speckit.amend` command | ❌ | ✅ Post-implementation spec amendment |
| `specify update` (CLI update check) | ❌ | ✅ |
| `specify hierarchy-contract` | ❌ | ✅ Program/Epic/Feature hierarchy validation |
| `specify scope-detect` | ❌ | ✅ Adaptive scope detection with gate-ready JSON |
| `specify scope-gate` | ❌ | ✅ Decomposition gate with follow/inspect/override |
| `specify productivity` cockpit | ❌ | ✅ `start` and `update` task management workflows |
| Scope gate contract module | ❌ | ✅ Typed strict/non-strict validation |
| Handoff metadata schema | ❌ | ✅ Structured handoff with provenance tracking |
| Orchestration contract module | ❌ | ✅ Typed orchestration contract validation |
| Enterprise compliance checker | ❌ | ✅ License, legal markers, trademark policy |
| Release deploy pipeline | ❌ | ✅ Automated VM deploy + Google Drive backup |
| Upstream compatibility opt-in | N/A | ✅ `--template-repo github/spec-kit` |
| Agent integrations | ✅ 18 named + "generic" catch-all | ✅ 18 named agents |
| Extension system | ✅ | ✅ |
| MIT license | ✅ | ✅ Preserved with attribution |

## Value Pillars

### 1. Structured Discovery (Phase 0)

AI agents work best when given clear, bounded objectives. Phase 0 transforms
vague ideas into ranked, scoped feature candidates before a single spec is
written. Commands: `/speckit.ideate`, `/speckit.select`, `/speckit.structure`,
`/speckit.validate`.

Key artifacts:

- `.spec-kit/ideas_backlog.md`
- `.spec-kit/idea_selection.md`
- `.spec-kit/ai_vision_canvas.md`
- `.spec-kit/vision_brief.md`
- `.spec-kit/approvals/g0-validation-report.md`

### 2. Executable Specifications

Specifications are not documents — they are contracts between human intent and
AI execution. The SDD workflow produces `.specify/specs/<feature>/spec.md`,
`plan.md`, and `tasks.md` as artifacts that agents directly consume.

Commands: `/speckit.constitution`, `/speckit.specify`, `/speckit.clarify`,
`/speckit.plan`, `/speckit.tasks`, `/speckit.implement`, `/speckit.amend`,
`/speckit.analyze`, `/speckit.checklist`, `/speckit.taskstoissues`.

### 3. Enterprise-Grade Governance

Every AI decision is traceable. The governance layer includes:

- **Scope gate contracts** (`specify scope-gate`, `specify scope-detect`):
  programmatic follow/inspect/override decisions with audit JSON.
- **Handoff metadata schema**: structured handoff records with provenance.
- **Orchestration contract module**: strict/non-strict typed validation.
- **Hierarchy contract** (`specify hierarchy-contract`): normalizes
  Program/Epic/Feature hierarchy payloads.
- **Compliance checker**: verifies license, legal markers, and trademark policy
  before each release.
- **Provenance playbook**: upstream intake with `git cherry-pick -x` for full
  commit-level traceability.

### 4. Broad Agent Integration Surface

18 AI coding agents are supported out of the box:

| Key | Agent | Type |
| --- | ----- | ---- |
| `claude` | Claude Code | CLI |
| `gemini` | Gemini CLI | CLI |
| `copilot` | GitHub Copilot | IDE |
| `cursor-agent` | Cursor | IDE |
| `qwen` | Qwen Code | CLI |
| `opencode` | opencode | CLI |
| `codex` | Codex CLI | CLI |
| `windsurf` | Windsurf | IDE |
| `kilocode` | Kilo Code | IDE |
| `auggie` | Auggie CLI | CLI |
| `roo` | Roo Code | IDE |
| `codebuddy` | CodeBuddy | CLI |
| `qoder` | Qoder CLI | CLI |
| `q` | Amazon Q Developer CLI | CLI |
| `amp` | Amp | CLI |
| `shai` | SHAI | CLI |
| `agy` | Antigravity | IDE |
| `bob` | IBM Bob | IDE |

New agents are added via a documented, convention-driven integration pattern
(see `AGENTS.md`). Use `specify init --ai <key>` to bootstrap any agent.

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
- All enhancements are additive and isolated. No upstream behavior is removed
  or replaced.
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
- [Supported Agents](agents.md) — Full agent reference with install URLs.
- [CLI Reference](cli.md) — Full CLI command reference.
- [Methodology](methodology.md) — SDD methodology and Phase 0 workflow.
