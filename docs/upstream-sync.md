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

## Keeping Fork Changes Isolated

- Prefer additive changes in `templates/`, `scripts/`, and documented overrides
- Avoid changing upstream-owned behavior unless required
- Keep `SPECIFY_TEMPLATE_REPO` override as the main fork distribution mechanism

## Compatibility Notes

When upstream evolves, prioritize:

1. Merging upstream improvements
2. Re-validating fork templates and scripts
3. Updating documentation as needed
