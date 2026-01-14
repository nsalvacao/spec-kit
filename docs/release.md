# Fork Release Process

This guide describes how to publish a release for the fork.

## 1) Update Version + Changelog

- Update version in `pyproject.toml`
- Add a changelog entry in `CHANGELOG.md`

**Versioning scheme:** use upstream base version with a fork suffix, e.g. `0.0.23-fork.1`.

Optional helper script (if used by upstream):

```bash
./.github/workflows/scripts/update-version.sh
```

## 2) Build Release Packages

```bash
./.github/workflows/scripts/create-release-packages.sh
```

This should generate zip assets under `.genreleases/`.

## 3) Create GitHub Release (Fork)

```bash
./.github/workflows/scripts/create-github-release.sh
```

Confirm the release tag and assets are published to `nsalvacao/spec-kit`.

## 4) Validate

- Install from the release tag
- Run `specify init` with `--template-repo nsalvacao/spec-kit`
- Confirm generated templates/scripts match fork expectations

## 5) Announce

- Update `README.md` badges if needed
- Reference the release in notes or documentation
