# Release Process

This guide describes how releases are published for this fork.

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

- Ensure `CHANGELOG.md` has the new version title.
- Ensure `## [Unreleased]` is reset for the next cycle.
- If needed, backfill missing headings for any tags created outside the normal
  release flow.
