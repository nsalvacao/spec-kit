# Walkthrough (Fork Workflow)

This guide walks through the full fork workflow: **Phase 0** followed by Spec‑Driven Development (SDD).

## 0) Install and Initialize

Install the forked CLI and initialize a project:

```bash
uv tool install specify-cli --from git+<https://github.com/nsalvacao/spec-kit.git>
specify init my-project --ai codex
```

Open the project folder and start your AI agent of choice.

## 1) Phase 0 — AI System Ideation (Recommended Prerequisite)

Phase 0 generates the artifacts that justify the project before specs are written.

1. **IDEATE**

   ```bash
   /speckit.ideate Generate 2–5 seed ideas and expand them using SCAMPER + HMW.
   ```

   Output: `.spec-kit/ideas_backlog.md`

2. **SELECT**

   ```bash
   /speckit.select Score all ideas with AI-RICE and pick the top candidate.
   ```

   Output: `.spec-kit/idea_selection.md`

   **AI-RICE Sensitivity Analysis**: The `calculate-ai-rice.sh` / `calculate-ai-rice.ps1`
   scripts include a built-in what-if sensitivity analysis. For each dimension, the output
   shows how the score changes with a ±1 variation, clamped to valid bounds:

   | Dimension | Bound |
   | --- | --- |
   | Reach | ≥ 1 (integer) |
   | Impact | Discrete steps: 0.25 → 0.5 → 1.0 → 2.0 → 3.0 |
   | Confidence | 0–100% |
   | Data\_Readiness | 0–100% |
   | Effort | ≥ 1 week |
   | Risk | 1–10 (integer) |

   A **Levers summary** at the end highlights the single most influential positive
   lever (action that most increases the score) and the most influential negative
   lever (action that most decreases the score), helping teams prioritize
   improvement efforts.

3. **STRUCTURE**

   ```bash
   /speckit.structure Build the AI Vision Canvas and a concise Vision Brief.
   ```

   Output: `.spec-kit/ai_vision_canvas.md`, `.spec-kit/vision_brief.md`

4. **VALIDATE**

   ```bash
   /speckit.validate Run Gate G0 checks and produce a decision report.
   ```

   Output: `.spec-kit/approvals/g0-validation-report.md`

## 2) Establish Project Constitution

```text
/speckit.constitution Create principles focused on code quality, testing standards, UX consistency, and performance.
```

Output: `.specify/memory/constitution.md`

## 3) Create the Specification

```text
/speckit.specify Describe the feature requirements, user stories, and constraints.
```

Output: `.specify/specs/<feature>/spec.md`

## 4) Clarify (Recommended)

```text
/speckit.clarify Review and clarify missing details before planning.
```

## 5) Create the Plan

```text
/speckit.plan Provide the tech stack and architecture choices.
```

Output: `.specify/specs/<feature>/plan.md`

## 6) Generate Tasks

```text
/speckit.tasks
```

Output: `.specify/specs/<feature>/tasks.md`

## 7) Analyze (Recommended)

```text
/speckit.analyze
```

Checks cross‑artifact consistency before execution.

## 8) Implement

```bash
/speckit.implement
```

Executes tasks according to the plan.

## 9) Amend (Post-Implementation)

```text
/speckit.amend Describe the edge case, new scenario, or behavioral correction.
```

Applies a targeted amendment when an edge case or correction is discovered
after implementation. Updates the spec, adds a failing test, then fixes the
code without re-running the full pipeline.

## 10) Checklist

```text
/speckit.checklist
```

Generates a quality checklist for the current feature.

## 11) Tasks to Issues

```text
/speckit.taskstoissues
```

Converts tasks into GitHub issues for project tracking.

## Troubleshooting Tips

- If you are not using git branches, set:

  ```bash
  export SPECIFY_FEATURE=001-your-feature
  ```

- If an agent tool is not installed, run `specify init --ignore-agent-tools`.
