# Provenance Playbook: Upstream PR Intake

This playbook provides step-by-step instructions for importing upstream PRs from
`github/spec-kit` into `nsalvacao/spec-kit` while preserving original authorship
and maintaining a complete provenance chain.

> **Related policy:** `docs/legal-compliance.md` (Section 3)
> **Related workflow:** `AGENTS.md` — Upstream PR Intake Workflow

---

## 1. Preparation

Before starting any intake, verify the current state of branches:

```bash
git fetch origin upstream --prune
git rev-parse --short origin/main
gh pr list -R nsalvacao/spec-kit --state open --json number,title,headRefName,baseRefName,url
```

Create or refresh a baseline branch from clean, synced `main`:

```bash
git checkout main
git pull origin main
git checkout -b baseline/upstream-intake-YYYY-MM-DD
git push origin baseline/upstream-intake-YYYY-MM-DD
```

---

## 2. Import Methods

### 2.1 Full PR head import (preferred)

When importing a complete upstream PR without modification:

```bash
# Add upstream remote if not already present
git remote add upstream https://github.com/github/spec-kit.git
git fetch upstream

# Create intake branch from baseline
git checkout baseline/upstream-intake-YYYY-MM-DD
git checkout -b intake/upstream-value-<topic>

# Merge the upstream PR branch
git merge upstream/<upstream-branch-name> --no-ff \
  -m "intake: import upstream PR #<N> — <short description>

Source PR: https://github.com/github/spec-kit/pull/<N>
Source branch: upstream/<upstream-branch-name>
Intake date: YYYY-MM-DD"

git push origin intake/upstream-value-<topic>
```

### 2.2 Cherry-pick with provenance flag

When cherry-picking individual upstream commits:

```bash
# Add upstream remote if not already present
git remote add upstream https://github.com/github/spec-kit.git
git fetch upstream

# Create intake branch from baseline
git checkout baseline/upstream-intake-YYYY-MM-DD
git checkout -b intake/upstream-value-<topic>

# Cherry-pick with -x to embed original SHA in commit message
git cherry-pick -x <upstream-sha1>
git cherry-pick -x <upstream-sha2>

git push origin intake/upstream-value-<topic>
```

> **Mandatory:** Always use `-x`. This appends `(cherry picked from commit <sha>)`
> to every commit message, creating an auditable link to the upstream origin.

### 2.3 Prohibited operations

The following operations **must never be used** when importing upstream commits:

```bash
# PROHIBITED — destroys original authorship
git cherry-pick --reset-author <sha>

# PROHIBITED — rewrites commit history
git rebase --root
git commit --amend --reset-author
```

---

## 3. Mandatory PR Metadata Template

Every upstream-intake PR **must** include the following metadata block in the PR
description. Copy and fill in all fields; leave none as `N/A` without a brief
reason.

```markdown
## Provenance

- **Source repository:** https://github.com/github/spec-kit
- **Source PR:** https://github.com/github/spec-kit/pull/<N>
- **Source commit(s):** <sha1>, <sha2>
- **Original author(s):** @<github-username>
- **Intake method:** <!-- cherry-pick -x | full PR head import -->
- **Intake branch:** intake/<topic>
- **Intake date:** YYYY-MM-DD
- **Baseline branch:** baseline/upstream-intake-YYYY-MM-DD

## Summary of changes

<!-- Briefly describe what this upstream PR adds or fixes -->

## Adaptation notes

<!-- Describe any conflict resolutions or adaptations made during intake.
     If the import is verbatim, write "No adaptation required." -->

## Compliance checklist

- [ ] Original authorship preserved (no `--reset-author` used)
- [ ] Cherry-picked commits use `-x` flag (SHA embedded in message)
- [ ] `LICENSE` and copyright notices intact
- [ ] CHANGELOG entry includes `Source PR:` provenance line
- [ ] No new trademark violations introduced
- [ ] CI compliance-guard passes on this PR
```

---

## 4. CHANGELOG Entry Format

For every upstream-intake PR, add a `CHANGELOG.md` entry under `## [Unreleased]`
with the following format:

```markdown
### Added | Changed | Fixed

- **Upstream PR #<N>: <description>**
  - <bullet describing the change>
  - Source PR: https://github.com/github/spec-kit/pull/<N>
```

The `Source PR:` line is required and is validated by the CI compliance-guard when
the entry contains `Upstream PR` or `upstream intake` keywords.

---

## 5. Seven-Step Intake Checklist

Use this checklist for every upstream intake batch. Tick each item before proceeding
to the next step.

1. [ ] **Baseline refreshed** — `baseline/upstream-intake-YYYY-MM-DD` is synced from
       `main`.
2. [ ] **Intake branch created** — one branch per upstream PR (`intake/<topic>`).
3. [ ] **Import method documented** — PR description uses the template in Section 3.
4. [ ] **Provenance preserved** — `-x` flag used for cherry-picks; no `--reset-author`.
5. [ ] **CI passes** — `compliance-guard`, `test`, and `lint` workflows are green.
6. [ ] **Baseline PR reviewed and merged** — `intake/* -> baseline/*` PR approved.
7. [ ] **Promotion PR opened** — `baseline/* -> main` PR ready for final review.

---

## 6. Verification Commands

After intake, verify authorship and provenance are intact:

```bash
# Verify commit author is the upstream author (not the importer)
git log --format="%H %an <%ae> %s" <intake-branch> ^baseline/upstream-intake-YYYY-MM-DD

# Verify cherry-pick provenance SHA is embedded
git log --format="%H %s %b" <intake-branch> ^baseline/upstream-intake-YYYY-MM-DD | grep "cherry picked"

# Run compliance checker locally
python scripts/python/compliance-checker.py check --repo-root .
```

---

## 7. References

- [`docs/legal-compliance.md`](legal-compliance.md) — full legal policy
- [`docs/upstream-sync.md`](upstream-sync.md) — upstream sync workflow
- [`AGENTS.md`](../AGENTS.md) — upstream PR intake safety policy
- [MIT License](https://opensource.org/license/mit)
- [GitHub Trademark Policy](https://docs.github.com/en/site-policy/other-site-policies/github-trademark-policy)
