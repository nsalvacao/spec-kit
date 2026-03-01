# Legal and Compliance Policy

This document codifies the legal obligations, attribution requirements, provenance
rules, and trademark-safe usage constraints that apply to the `nsalvacao/spec-kit`
fork and all redistribution paths derived from it.

> **Compliance marker**: `legal-compliance:v1`

---

## 1. MIT License Obligations

This repository is distributed under the [MIT License](../LICENSE).

**Mandatory obligations for all redistribution paths:**

1. **Include the LICENSE file.** Every release artifact (zip package, tarball,
   Docker image, etc.) must contain a verbatim copy of `LICENSE` at the archive root.
2. **Preserve copyright notices.** Do not remove, modify, or obscure the copyright
   notice in `LICENSE` (`Copyright GitHub, Inc.`).
3. **No additional restrictions.** Do not attach additional license terms that
   conflict with the MIT grant (e.g., non-commercial clauses, additional warranty
   disclaimers that narrow the grant).
4. **Attribution in documentation.** Published documentation must acknowledge the
   MIT license and the upstream origin. The phrase "MIT-licensed fork of
   `github/spec-kit`" (or equivalent) fulfils this requirement.

**Enforcement:** The CI compliance-guard workflow (`compliance-guard.yml`) verifies
that the `LICENSE` file is present and that key documents contain the required
compliance markers. See Section 5 for CI details.

---

## 2. Fork Attribution Requirements

This fork (`nsalvacao/spec-kit`) is an independent derivative of
`github/spec-kit`. The following attribution rules apply:

1. **Repository description** must note the upstream origin. The phrase
   "Independent fork of `github/spec-kit`" (or equivalent) must appear in
   `README.md` and in the repository About field on GitHub.
2. **Non-affiliation disclaimer** must be present and clearly visible in `README.md`.
   Accepted phrasing: *"This fork is not affiliated with GitHub."*
3. **Changelog upstream credits.** Whenever a change originates from an upstream
   PR or commit, the `CHANGELOG.md` entry must include a provenance line in the
   format:

   ```text
   Source PR: https://github.com/github/spec-kit/pull/<N>
   ```

   or equivalent (see Section 3 for details).

4. **Derived documents** (docs, templates, scripts) that are direct copies or
   near-verbatim adaptations of upstream files must retain the original copyright
   header if one exists, or add the attribution comment:

   ```text
   # Originally from github/spec-kit — MIT License
   ```

---

## 3. Upstream Intake Provenance Rules

When selectively importing upstream commits or PRs, the following rules are mandatory
to maintain an auditable provenance chain:

### 3.1 Cherry-pick provenance

Always use the `-x` flag when cherry-picking upstream commits. This appends the
original commit SHA to the commit message, creating a verifiable link:

```bash
git cherry-pick -x <upstream-sha>
```

### 3.2 Author preservation

Never reset authorship when importing upstream commits. The following flag is
**prohibited**:

```bash
# PROHIBITED — do not use
git cherry-pick --reset-author <sha>
```

The original author and committer metadata must remain intact.

### 3.3 PR metadata template

Every upstream-intake PR must include the following metadata block in the PR
description (also see `docs/provenance-playbook.md` for the full template):

```text
## Provenance

- Source repository: https://github.com/github/spec-kit
- Source PR: https://github.com/github/spec-kit/pull/<N>
- Source commit(s): <sha1>, <sha2>
- Original author(s): @<github-username>
- Intake method: cherry-pick -x | full PR head import
- Intake branch: intake/<topic>
- Intake date: YYYY-MM-DD
```

### 3.4 CHANGELOG provenance entries

For upstream-intake releases, `CHANGELOG.md` entries that originate from upstream
must include:

```text
Source PR: https://github.com/github/spec-kit/pull/<N>
```

The CI compliance guard checks for this marker when an entry contains the trigger
phrase `Upstream PR` or `upstream intake` (case-insensitive).

---

## 4. Trademark-Safe Usage Constraints

### 4.1 GitHub® trademark

GitHub® is a registered trademark of GitHub, Inc. (a Microsoft subsidiary).
Usage of "GitHub" in this fork is **attribution-only**: it identifies the upstream
project origin. The following rules apply:

- **Permitted:** "Independent fork of `github/spec-kit`", "based on GitHub Spec Kit",
  "upstream: `github/spec-kit`".
- **Not permitted:** Product names or titles that incorporate "GitHub" as a primary
  identifier (e.g., "GitHub Nexo", "GitHub Spec Kit Pro").
- **Not permitted:** Use of GitHub logos, Octocat, or any GitHub-owned visual marks.
- **Not permitted:** Phrasing that implies GitHub sponsorship, endorsement, or
  affiliation (e.g., "officially extended GitHub Spec Kit").

### 4.2 Spec Kit™ trademark

Spec Kit™ may be a trademark of GitHub, Inc. Usage must follow the same
attribution-only principle:

- Reference "Spec Kit" only to identify the upstream origin.
- This fork's public product name is **Nexo Spec Kit** — an independent name.
- Do not register "Spec Kit" as part of the fork's own trademark.

### 4.3 Non-affiliation statement

All user-facing documentation (README, website, CLI help text) must include a
clearly visible non-affiliation statement. Accepted phrasing:

> This fork is **not affiliated with GitHub**.
> Trademark usage is attribution-only. See `docs/trademarks.md`.

### 4.4 Visual brand usage

- Do not use GitHub logos or the Octocat mascot in this fork's branding materials.
- The fork may use its own logo (Nexo Spec Kit logo) without restriction.
- CI badge references to GitHub Actions are permitted as functional links.

---

## 5. CI Compliance Guards

The workflow `.github/workflows/compliance-guard.yml` runs on every push and pull
request to enforce the following gates automatically:

| Check | Trigger | Failure action |
|---|---|---|
| `LICENSE` file present at repo root | Always | Block PR |
| `legal-compliance:v1` marker in `docs/legal-compliance.md` | Always | Block PR |
| Non-affiliation statement in `README.md` | Always | Block PR |
| MIT license reference in `README.md` | Always | Block PR |
| Upstream provenance marker in `CHANGELOG.md` entries | When `Upstream PR` or `upstream intake` keyword present | Block PR |
| `docs/trademarks.md` trademark notice present | Always | Block PR |

The checker is implemented in `scripts/python/compliance-checker.py` and exits
non-zero when any gate fails, causing the CI job to fail.

---

## 6. Release Compliance Gate

Before publishing any release, the release checklist in `docs/release.md` requires
an explicit compliance gate (Section 2.5). The following must all pass:

1. `compliance-guard` CI workflow is green on the release commit.
2. Release artifact packages include `LICENSE` at root.
3. `CHANGELOG.md` version entry is present with all upstream credits.
4. Non-affiliation statement is visible in `README.md`.
5. No new trademark violations introduced (review `docs/trademarks.md`).

---

## 7. Contribution Compliance

Contributors must acknowledge the following in their PRs:

- Contributions are licensed under MIT (DCO-equivalent commitment).
- If importing upstream code, the provenance rules in Section 3 apply.
- AI-assisted contributions require disclosure per `CONTRIBUTING.md`.

---

## 8. References

- [MIT License text](https://opensource.org/license/mit)
- [GitHub Trademark Policy](https://docs.github.com/en/site-policy/other-site-policies/github-trademark-policy)
- [GitHub Logo Policy](https://docs.github.com/en/site-policy/other-site-policies/github-logo-policy)
- [GitHub Terms of Service](https://docs.github.com/en/site-policy/github-terms/github-terms-of-service)
- [Microsoft Trademark and Brand Guidelines](https://www.microsoft.com/en-us/legal/intellectualproperty/trademarks)
- [USPTO Trademark Basics](https://www.uspto.gov/trademarks/basics)
- [`docs/trademarks.md`](trademarks.md) — fork-specific trademark notice
- [`docs/provenance-playbook.md`](provenance-playbook.md) — step-by-step intake guide
- [`docs/upstream-sync.md`](upstream-sync.md) — upstream synchronization workflow
- [`AGENTS.md`](../AGENTS.md) — upstream intake safety policy
