# Google Drive Release Backup

This document describes the automated release backup flow to personal Google Drive.

## Overview

The workflow `.github/workflows/backup-gdrive.yml` runs on:

- `release: published`
- manual `workflow_dispatch`

For each release tag, it creates:

- deterministic source archive (`.tar.gz`)
- checksum (`.sha256`)
- manifest (`.manifest.json`)

Then it uploads (or updates) those files into a configured Drive folder by ID.

## Authentication model

The workflow uses OAuth 2.0 refresh-token flow (no manual intervention per run):

- refresh token -> short-lived access token at runtime
- Drive API uploads through `files` upload endpoints

This model is selected for personal Google account compatibility.

## Required repository configuration

Set the following **repository secrets**:

- `GDRIVE_OAUTH_CLIENT_ID`
- `GDRIVE_OAUTH_CLIENT_SECRET`
- `GDRIVE_OAUTH_REFRESH_TOKEN`

Set the following **repository variables**:

- `GDRIVE_BACKUP_FOLDER_ID`
- `GDRIVE_BACKUP_RETENTION_COUNT` (optional, default: `30`)

## Runtime behavior

1. Resolve release tag and commit SHA.
2. Package source from git tag using `git archive`.
3. Generate checksum and manifest.
4. Refresh OAuth access token.
5. Upsert 3 files in Drive folder:
   - `<prefix>-<tag>.tar.gz`
   - `<prefix>-<tag>.tar.gz.sha256`
   - `<prefix>-<tag>.manifest.json`
6. Apply manifest-based retention policy (keep newest `N` backup sets).

Default prefix: `spec-kit-release-backup`.

## Dry-run mode

Manual runs support dry-run:

- `workflow_dispatch` input `dry_run=true` (default for manual runs)

Dry-run still prepares artifacts and validates auth/config path, but it does not mutate Drive files.

## Observability

The workflow writes append-only timeline notes in `GITHUB_STEP_SUMMARY`, including:

- release target resolution
- config resolution (redacted folder suffix only)
- artifact metadata
- upload result JSON
- retention summary

It also uploads local run artifacts:

- `backup-result.json`
- generated `.sha256`
- generated `.manifest.json`

## Security notes

- Never hardcode credentials in repository files.
- Keep OAuth values only in repository secrets.
- Do not print tokens or full folder IDs in logs.
- Rotate refresh token and client secret periodically.

## Troubleshooting

- `invalid_grant`: refresh token is expired/revoked or OAuth client mismatch.
- `insufficientPermissions`: OAuth scope/config mismatch for Drive API.
- `404 notFound`: folder ID is invalid or inaccessible by authenticated user.
- `429/5xx`: workflow applies retry/backoff automatically.

## Internal runbook

For private operational details and environment-specific setup:

- `D:\VM-GCP-Github-Deploy\backup-github-gdrive.md`
- `D:\VM-GCP-Github-Deploy\` supporting notes/scripts
