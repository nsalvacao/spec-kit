# Release Process

This guide describes how releases are published for this fork.

## 0) Automation Baseline

Release metadata consistency is governed by:

- Policy file: `.github/release-version-policy.yml`
- Guard workflow: `.github/workflows/release-consistency-guard.yml`
- Sync workflow: `.github/workflows/release-metadata-sync.yml`
- Hygiene workflow: `.github/workflows/branch-hygiene.yml`

The guard validates version/changelog/runtime coherence. The sync workflow opens a PR (never pushes directly to `main`) when release metadata drift is detected.

## 1) Versioning Rules

- Use SemVer in `pyproject.toml` (for example: `0.0.35`).
- Keep release tags aligned with published template bundles (`vX.Y.Z`).
- Do not use the legacy `-fork.N` suffix for new releases.

## 2) Changelog Rules (Keep a Changelog)

Before publishing a release:

1. Keep active work only under `## [Unreleased]`.
2. Create a new version heading:
   - `## [X.Y.Z] - YYYY-MM-DD`
3. Move relevant entries from `Unreleased` into that version.
4. Use standard sections when applicable:
   - `### Added`
   - `### Changed`
   - `### Fixed`
   - `### Security`

If a tag was published without detailed curated notes, add the version heading
and include at least a release-notes link to keep the changelog version-indexed.

## 3) Build Release Packages

```bash
./.github/workflows/scripts/create-release-packages.sh
```

This generates zip assets under `.genreleases/`.

## 4) Create GitHub Release

```bash
./.github/workflows/scripts/create-github-release.sh
```

Confirm the tag and assets are published to `nsalvacao/spec-kit`.

## 5) Validate

- Install from the release tag.
- Run `specify init` with `--template-repo nsalvacao/spec-kit`.
- Confirm generated templates/scripts match fork expectations.

## 6) Post-Release Hygiene

- Metadata drift is handled by `release-metadata-sync.yml`, which opens/updates:
  - `automation/release-metadata-vX.Y.Z` -> `main`
- `release-consistency-guard.yml` blocks PRs to `main` when coherence fails.
- Nightly monitor mode opens/updates a drift issue when metadata remains inconsistent.

## 7) Local Main Hygiene

Use the helper scripts before starting new implementation branches:

```bash
scripts/bash/sync-main.sh
```

PowerShell:

```powershell
scripts/powershell/sync-main.ps1
```

Default mode is dry-run for stale local branch cleanup. Pass `--apply` (bash) or `-Apply` (PowerShell) to delete local branches whose upstream is `[gone]`.
