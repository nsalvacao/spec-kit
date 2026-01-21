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

## Troubleshooting Tips

- If you are not using git branches, set:

  ```bash
  export SPECIFY_FEATURE=001-your-feature
  ```

- If an agent tool is not installed, run `specify init --ignore-agent-tools`.
