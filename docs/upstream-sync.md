# Upstream Sync Guide

This fork tracks the upstream repository (`github/spec-kit`) while keeping fork-specific enhancements isolated and compatible.

## Recommended Workflow

1. Add the upstream remote (once):

   ```bash
   git remote add upstream <https://github.com/github/spec-kit.git>
   ```

2. Fetch upstream:

   ```bash
   git fetch upstream --prune
   ```

3. Merge or rebase upstream into your working branch:

   ```bash
   git merge upstream/main
   # or
   git rebase upstream/main
   ```

4. Resolve conflicts and run tests (at least Phase 0 E2E scripts).

5. Push your fork branch back to `origin`.

## Selective Intake Preflight (Mandatory)

Before starting any upstream intake batch, run:

```bash
git fetch origin upstream --prune
git rev-parse --short origin/main
gh pr list -R nsalvacao/spec-kit --state open --json number,title,headRefName,baseRefName,url
```

Treat these live values as source of truth. Do not rely on stale handoff snapshots for SHAs, branch state, or PR counts.

## Single-Lane Intake Policy

For selective upstream PR intake, use one lane consistently across the full batch:

- Intake branches: `intake/lote-<A|B|C>-pr-<upstream_pr_number>`
- Review PR target: `baseline/main-sync-YYYY-MM-DD`
- Promotion PR target (after batch): `main`

Do not mix intake flow (`intake -> baseline`) with feature flow (`feat -> main`) in the same intake batch unless explicitly requested by repository owner.

## Intake Validation Commands

```bash
uv run pytest tests/ --tb=short
git ls-files -z '*.md' ':!:extensions/**' | xargs -0 npx markdownlint-cli2
```

The markdown command above avoids local untracked/archive noise and aligns with CI-relevant tracked files.

## Keeping Fork Changes Isolated

- Prefer additive changes in `templates/`, `scripts/`, and documented overrides
- Avoid changing upstream-owned behavior unless required
- Keep `SPECIFY_TEMPLATE_REPO` override as the main fork distribution mechanism

## Compatibility Notes

When upstream evolves, prioritize:

1. Merging upstream improvements
2. Re-validating fork templates and scripts
3. Updating documentation as needed
