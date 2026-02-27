# Release Process

This guide describes how releases are published for this fork.

## 0) Automation Baseline

Release metadata consistency is governed by:

- Policy file: `.github/release-version-policy.yml`
- Manifest file: `.github/version-map.yml`
- Guard workflow: `.github/workflows/release-consistency-guard.yml`
- Coherence workflow: `.github/workflows/version-coherence.yml`
- Sync workflow: `.github/workflows/release-metadata-sync.yml`
- Hygiene workflow: `.github/workflows/branch-hygiene.yml`
- Baseline sync workflow: `.github/workflows/baseline-auto-sync.yml`
- Deploy workflow: `.github/workflows/deploy.yml`
- Bump helpers:
  - `scripts/bash/version-bump.sh`
  - `scripts/powershell/version-bump.ps1`

The guard validates release metadata coherence. The version coherence workflow validates canonical version propagation using the manifest map. The sync workflow opens a PR (never pushes directly to `main`) when metadata drift is detected.
The deploy workflow installs `specify-cli` on a configured VM whenever a GitHub Release is published.

Authority split:

- `.github/version-map.yml` is the source of truth for version propagation (`pyproject.toml`, `uv.lock`, changelog/runtime/tag checks).
- `.github/release-version-policy.yml` governs release guard and branch hygiene policy behavior.

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

## 2.1) Version Bump Orchestration

Use the manifest-driven bump helpers to keep `pyproject.toml`, `uv.lock`, and
`CHANGELOG.md` synchronized:

```bash
scripts/bash/version-bump.sh --part patch --dry-run --include-diff
scripts/bash/version-bump.sh --part patch
```

PowerShell:

```powershell
scripts/powershell/version-bump.ps1 -Part patch -DryRun -IncludeDiff
scripts/powershell/version-bump.ps1 -Part patch
```

To add new managed targets safely:

1. Add the file and regex capture rule to `.github/version-map.yml`.
2. Keep the regex scoped and deterministic with one `version` capture group.
3. Add the target path to `sync.allowlist`.
4. Run `python scripts/python/version-orchestrator.py check --skip-runtime`.

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
- The sync workflow enforces file safety using `allowlist` from `.github/version-map.yml`.
- `release-consistency-guard.yml` blocks PRs to `main` when coherence fails.
- `version-coherence.yml` blocks PRs to `main` when mapped version drift is detected.
- `baseline-auto-sync.yml` auto-triggers "Update branch" for open `baseline/* -> main`
  PRs when `main` moves ahead, reducing manual sync drift in parallel work.
- Nightly monitor mode opens/updates a drift issue when metadata remains inconsistent.

### 6.1) Release Deploy to VM

The deploy workflow can be triggered automatically on `release: published` or manually (`workflow_dispatch`).

Required repository secrets:

- `DEPLOY_VM_HOST`
- `DEPLOY_VM_USER`
- `DEPLOY_SSH_KEY`

Required repository variable:

- `DEPLOY_VM_HOST_FINGERPRINT` (for example `SHA256:...`)
  - Supports one or more comma-separated fingerprints for controlled key-rotation windows.
- `DEPLOY_VM_KNOWN_HOSTS` (pre-pinned known_hosts content for the target VM)
  - Example generator: `ssh-keyscan -T 10 -p 22 -t ed25519 <DEPLOY_VM_HOST> | sed '/^#/d' | head -n 1`

Optional repository variables:

- `DEPLOY_VM_PORT` (defaults to `22`)

Notes:

- Deploy uses absolute paths (`~/.local/bin/uv`, `~/.local/bin/specify`) because non-interactive SSH sessions do not load shell profiles.
- Deploy uses native `ssh` in the runner (no third-party SSH action dependency).
- Host key is verified by matching pre-pinned known_hosts content against `DEPLOY_VM_HOST_FINGERPRINT`.
- If VM host keys rotate, update `DEPLOY_VM_HOST_FINGERPRINT` before the next release deploy.
- If VM host keys rotate, update `DEPLOY_VM_KNOWN_HOSTS` before the next release deploy.
- Manual runs accept an optional `tag` input and validate `vMAJOR.MINOR.PATCH` format.
- Smoke test runs `specify --help` remotely after install.
- VM bootstrap must ensure both binaries exist at those paths:
  - `~/.local/bin/uv`
  - `~/.local/bin/specify`

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
