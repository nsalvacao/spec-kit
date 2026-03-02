# Walkthrough (Fork Workflow)

This guide walks through the full fork workflow: **Phase 0** followed by Spec‑Driven Development (SDD).

## 0) Install and Initialize

Install the forked CLI and initialize a project:

```bash
uv tool install specify-cli --from git+<https://github.com/nsalvacao/spec-kit.git>
specify init my-project --ai codex
```

Open the project folder and start your AI agent of choice.

## 1) Strategy Pre-Phase (Optional but Recommended)

Use strategic brainstorm when you need a deeper expansion pass before Phase 0:

```bash
/speckit.brainstorm Run the 8-framework strategic brainstorm and generate .ideas/brainstorm-expansion.md.
```

Output: `.ideas/brainstorm-expansion.md`

The result complements (does not replace) Phase 0. Use it as context for IDEATE.

## 2) Phase 0 — AI System Ideation (Recommended Prerequisite)

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

## 3) Establish Project Constitution

```text
/speckit.constitution Create principles focused on code quality, testing standards, UX consistency, and performance.
```

Output: `.specify/memory/constitution.md`

## 4) Create the Specification

```text
/speckit.specify Describe the feature requirements, user stories, and constraints.
```

Output: `.specify/specs/<feature>/spec.md`

## 5) Clarify (Recommended)

```text
/speckit.clarify Review and clarify missing details before planning.
```

## 6) Create the Plan

```text
/speckit.plan Provide the tech stack and architecture choices.
```

Output: `.specify/specs/<feature>/plan.md`

## 7) Generate Tasks

```text
/speckit.tasks
```

Output: `.specify/specs/<feature>/tasks.md`

## 8) Analyze (Recommended)

```text
/speckit.analyze
```

Checks cross‑artifact consistency before execution.

## 9) Implement

```bash
/speckit.implement
```

Executes tasks according to the plan.

## 10) Amend (Post-Implementation)

```text
/speckit.amend Describe the edge case, new scenario, or behavioral correction.
```

Applies a targeted amendment when an edge case or correction is discovered
after implementation. Updates the spec, adds a failing test, then fixes the
code without re-running the full pipeline.

## 11) Checklist

```text
/speckit.checklist
```

Generates a quality checklist for the current feature.

## 12) Tasks to Issues

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
