#!/usr/bin/env python3
"""Release backup uploader for Google Drive (OAuth refresh-token flow)."""

from __future__ import annotations

import argparse
import hashlib
import json
import mimetypes
import os
import random
import re
import string
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


DRIVE_FILES_API = "https://www.googleapis.com/drive/v3/files"
DRIVE_UPLOAD_API = "https://www.googleapis.com/upload/drive/v3/files"
OAUTH_TOKEN_API = "https://oauth2.googleapis.com/token"
RETRYABLE_STATUS_CODES = {408, 429, 500, 502, 503, 504}
FOLDER_ID_PATTERN = re.compile(r"^[A-Za-z0-9_-]{10,}$")
SENSITIVE_JSON_PATTERN = re.compile(
    r'(?i)("?(?:access_token|refresh_token|client_secret|id_token)"?\s*[:=]\s*")([^"]+)(")'
)
SENSITIVE_QUERY_PATTERN = re.compile(r"(?i)\b(refresh_token|access_token|client_secret)=([^&\s]+)")


class DriveBackupError(ValueError):
    """Raised when backup creation/upload fails."""


@dataclass(frozen=True)
class UploadArtifact:
    """Artifact upload contract."""

    name: str
    path: Path
    mime_type: str


def _redact_sensitive_text(raw: str) -> str:
    text = SENSITIVE_JSON_PATTERN.sub(r"\1***REDACTED***\3", raw)
    text = SENSITIVE_QUERY_PATTERN.sub(r"\1=***REDACTED***", text)
    return text


def _escape_drive_query_literal(value: str) -> str:
    return value.replace("\\", "\\\\").replace("'", "\\'")


def _normalize_folder_id(raw_value: str) -> str:
    folder_id = raw_value.strip()
    if FOLDER_ID_PATTERN.fullmatch(folder_id) is None:
        raise DriveBackupError(
            "folder id is invalid: expected Google Drive folder ID format ([A-Za-z0-9_-]{10,})."
        )
    return folder_id


def _utc_now() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def _append_summary(summary_file: Path | None, message: str) -> None:
    if summary_file is None:
        return
    summary_file.parent.mkdir(parents=True, exist_ok=True)
    with summary_file.open("a", encoding="utf-8") as handle:
        handle.write(f"- [{_utc_now()}] {message}\n")


def _read_json_bytes(payload: bytes | None) -> dict[str, Any]:
    if not payload:
        return {}
    try:
        parsed = json.loads(payload.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return {}
    return parsed if isinstance(parsed, dict) else {}


def _extract_retry_after(headers: dict[str, str], body: dict[str, Any]) -> int | None:
    for key in ("retry-after", "Retry-After"):
        value = headers.get(key)
        if value and value.strip().isdigit():
            return int(value.strip())

    error_block = body.get("error")
    if isinstance(error_block, dict):
        details = error_block.get("details")
        if isinstance(details, list):
            for detail in details:
                if isinstance(detail, dict):
                    retry = detail.get("retryDelay")
                    if isinstance(retry, str) and retry.endswith("s"):
                        raw = retry[:-1]
                        if raw.isdigit():
                            return int(raw)

    retry_after = body.get("retry_after")
    if isinstance(retry_after, int) and retry_after >= 0:
        return retry_after
    if isinstance(retry_after, str) and retry_after.isdigit():
        return int(retry_after)
    return None


def _request(
    *,
    method: str,
    url: str,
    headers: dict[str, str] | None = None,
    body: bytes | None = None,
    retries: int = 4,
    timeout_seconds: int = 90,
    summary_file: Path | None = None,
    context: str = "request",
) -> tuple[dict[str, Any], dict[str, str], int]:
    request_headers = dict(headers or {})
    attempt = 0
    while True:
        attempt += 1
        request = urllib.request.Request(url=url, data=body, headers=request_headers, method=method)
        try:
            with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
                raw_body = response.read()
                response_headers = dict(response.headers.items())
                parsed_body = _read_json_bytes(raw_body)
                code = int(getattr(response, "status", 200))
                return parsed_body, response_headers, code
        except urllib.error.HTTPError as exc:
            raw = exc.read()
            parsed_error = _read_json_bytes(raw)
            response_headers = dict(exc.headers.items()) if exc.headers else {}
            code = int(exc.code)
            retry_after = _extract_retry_after(response_headers, parsed_error)
            if code in RETRYABLE_STATUS_CODES and attempt <= retries:
                delay = (
                    float(retry_after)
                    if retry_after is not None
                    else min(2 ** attempt, 16) + random.uniform(0.0, 1.0)
                )
                _append_summary(
                    summary_file,
                    (
                        f"{context}: HTTP {code} (attempt {attempt}/{retries + 1}) -> "
                        f"retrying in {delay:.2f}s"
                    ),
                )
                time.sleep(delay)
                continue
            detail = (
                parsed_error.get("error_description")
                or parsed_error.get("error")
                or parsed_error
                or raw.decode("utf-8", errors="replace")
            )
            redacted_detail = _redact_sensitive_text(str(detail))
            raise DriveBackupError(f"{context}: HTTP {code}: {redacted_detail}") from exc
        except urllib.error.URLError as exc:
            if attempt <= retries:
                delay = min(2 ** attempt, 16) + random.uniform(0.0, 1.0)
                _append_summary(
                    summary_file,
                    (
                        f"{context}: network error '{exc.reason}' "
                        f"(attempt {attempt}/{retries + 1}) -> retrying in {delay:.2f}s"
                    ),
                )
                time.sleep(delay)
                continue
            raise DriveBackupError(f"{context}: network failure: {exc.reason}") from exc


def _refresh_access_token(
    *,
    client_id: str,
    client_secret: str,
    refresh_token: str,
    summary_file: Path | None = None,
) -> tuple[str, dict[str, Any]]:
    form_payload = urllib.parse.urlencode(
        {
            "client_id": client_id,
            "client_secret": client_secret,
            "refresh_token": refresh_token,
            "grant_type": "refresh_token",
        }
    ).encode("utf-8")

    body, _, _ = _request(
        method="POST",
        url=OAUTH_TOKEN_API,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        body=form_payload,
        retries=2,
        summary_file=summary_file,
        context="oauth-token-refresh",
    )
    token = str(body.get("access_token", "")).strip()
    if not token:
        raise DriveBackupError("oauth-token-refresh: response did not include access_token.")
    return token, body


def _sha256_hex(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _ensure_artifact(path: Path) -> None:
    if not path.exists() or not path.is_file():
        raise DriveBackupError(f"artifact does not exist: {path}")
    if path.stat().st_size <= 0:
        raise DriveBackupError(f"artifact is empty: {path}")


def _derive_names(artifact_name: str) -> tuple[str, str]:
    if artifact_name.endswith(".tar.gz"):
        stem = artifact_name[: -len(".tar.gz")]
    else:
        stem = artifact_name.rsplit(".", 1)[0]
    checksum_name = f"{artifact_name}.sha256"
    manifest_name = f"{stem}.manifest.json"
    return checksum_name, manifest_name


def _write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _mime_for(path: Path, fallback: str) -> str:
    guessed, _ = mimetypes.guess_type(str(path))
    return guessed or fallback


def _multipart_body(metadata: dict[str, Any], path: Path, mime_type: str) -> tuple[bytes, str]:
    boundary = "===============%s==" % "".join(random.choices(string.ascii_letters + string.digits, k=24))
    metadata_bytes = json.dumps(metadata, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    file_bytes = path.read_bytes()
    body = b"".join(
        [
            f"--{boundary}\r\n".encode("utf-8"),
            b"Content-Type: application/json; charset=UTF-8\r\n\r\n",
            metadata_bytes,
            b"\r\n",
            f"--{boundary}\r\n".encode("utf-8"),
            f"Content-Type: {mime_type}\r\n\r\n".encode("utf-8"),
            file_bytes,
            b"\r\n",
            f"--{boundary}--\r\n".encode("utf-8"),
        ]
    )
    return body, boundary


def _drive_query_url(*, query: str, fields: str, page_size: int = 50, order_by: str | None = None) -> str:
    params: dict[str, str] = {
        "q": query,
        "fields": fields,
        "pageSize": str(page_size),
        "supportsAllDrives": "true",
        "includeItemsFromAllDrives": "true",
        "corpora": "allDrives",
    }
    if order_by:
        params["orderBy"] = order_by
    return f"{DRIVE_FILES_API}?{urllib.parse.urlencode(params)}"


def _find_files_by_name(
    *,
    token: str,
    folder_id: str,
    name: str,
    summary_file: Path | None = None,
) -> list[dict[str, str]]:
    safe_folder_id = _escape_drive_query_literal(folder_id)
    safe_name = _escape_drive_query_literal(name)
    query = f"'{safe_folder_id}' in parents and trashed=false and name='{safe_name}'"
    payload, _, _ = _request(
        method="GET",
        url=_drive_query_url(
            query=query,
            fields="files(id,name,createdTime)",
            page_size=20,
            order_by="createdTime desc",
        ),
        headers={"Authorization": f"Bearer {token}", "Accept": "application/json"},
        summary_file=summary_file,
        context=f"drive-find-file:{name}",
    )
    files = payload.get("files")
    if not isinstance(files, list):
        return []
    normalized: list[dict[str, str]] = []
    for item in files:
        if isinstance(item, dict):
            file_id = str(item.get("id", "")).strip()
            file_name = str(item.get("name", "")).strip()
            created_time = str(item.get("createdTime", "")).strip()
            if file_id and file_name:
                normalized.append({"id": file_id, "name": file_name, "createdTime": created_time})
    return normalized


def _assert_folder_access(
    *,
    token: str,
    folder_id: str,
    summary_file: Path | None = None,
) -> dict[str, str]:
    payload, _, _ = _request(
        method="GET",
        url=(
            f"{DRIVE_FILES_API}/{folder_id}"
            "?supportsAllDrives=true&fields=id,name,mimeType,trashed"
        ),
        headers={"Authorization": f"Bearer {token}", "Accept": "application/json"},
        summary_file=summary_file,
        context="drive-folder-access-check",
    )
    resolved_id = str(payload.get("id", "")).strip()
    resolved_name = str(payload.get("name", "")).strip()
    mime_type = str(payload.get("mimeType", "")).strip()
    trashed = bool(payload.get("trashed", False))
    if resolved_id != folder_id:
        raise DriveBackupError(
            "drive-folder-access-check: resolved folder id mismatch for configured target."
        )
    if mime_type != "application/vnd.google-apps.folder":
        raise DriveBackupError(
            "drive-folder-access-check: configured folder id does not reference a Drive folder."
        )
    if trashed:
        raise DriveBackupError("drive-folder-access-check: configured folder is in trash.")

    _append_summary(
        summary_file,
        f"drive-folder-access-check: ok (folder_name={resolved_name}, folder_id_suffix={folder_id[-8:]})",
    )
    return {"id": resolved_id, "name": resolved_name}


def _upload_artifact(
    *,
    token: str,
    folder_id: str,
    artifact: UploadArtifact,
    app_properties: dict[str, str],
    dry_run: bool,
    summary_file: Path | None = None,
) -> dict[str, str]:
    existing = _find_files_by_name(token=token, folder_id=folder_id, name=artifact.name, summary_file=summary_file)
    existing_id = existing[0]["id"] if existing else None
    action = "update" if existing_id else "create"

    if dry_run:
        _append_summary(
            summary_file,
            (
                f"dry-run upload {action}: name={artifact.name}, size_bytes={artifact.path.stat().st_size}, "
                f"mime={artifact.mime_type}, existing_id={existing_id or 'none'}"
            ),
        )
        return {"id": existing_id or "dry-run", "name": artifact.name, "action": f"dry-run-{action}"}

    metadata: dict[str, Any] = {"name": artifact.name, "appProperties": app_properties}
    if existing_id is None:
        metadata["parents"] = [folder_id]
        url = f"{DRIVE_UPLOAD_API}?uploadType=multipart&supportsAllDrives=true"
        method = "POST"
    else:
        url = f"{DRIVE_UPLOAD_API}/{existing_id}?uploadType=multipart&supportsAllDrives=true"
        method = "PATCH"

    payload, boundary = _multipart_body(metadata=metadata, path=artifact.path, mime_type=artifact.mime_type)
    response, _, _ = _request(
        method=method,
        url=url,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": f"multipart/related; boundary={boundary}",
            "Accept": "application/json",
        },
        body=payload,
        summary_file=summary_file,
        context=f"drive-upload:{artifact.name}",
    )
    uploaded_id = str(response.get("id", "")).strip()
    if not uploaded_id:
        raise DriveBackupError(f"drive-upload:{artifact.name}: missing file id in API response.")
    _append_summary(
        summary_file,
        f"upload {action} success: name={artifact.name}, file_id_suffix={uploaded_id[-8:]}",
    )
    return {"id": uploaded_id, "name": artifact.name, "action": action}


def _delete_file(
    *,
    token: str,
    file_id: str,
    dry_run: bool,
    summary_file: Path | None = None,
) -> None:
    if dry_run:
        _append_summary(summary_file, f"dry-run retention delete: file_id_suffix={file_id[-8:]}")
        return
    _request(
        method="DELETE",
        url=f"{DRIVE_FILES_API}/{file_id}?supportsAllDrives=true",
        headers={"Authorization": f"Bearer {token}", "Accept": "application/json"},
        summary_file=summary_file,
        context=f"drive-delete:{file_id[-8:]}",
    )


def _apply_retention(
    *,
    token: str,
    folder_id: str,
    keep_count: int,
    prefix: str,
    dry_run: bool,
    summary_file: Path | None = None,
) -> dict[str, Any]:
    if keep_count <= 0:
        raise DriveBackupError("retention count must be >= 1")

    safe_prefix = _escape_drive_query_literal(prefix)
    safe_folder_id = _escape_drive_query_literal(folder_id)
    query = (
        f"'{safe_folder_id}' in parents and trashed=false and "
        f"name contains '{safe_prefix}' and name contains '.manifest.json'"
    )
    payload, _, _ = _request(
        method="GET",
        url=_drive_query_url(
            query=query,
            fields="files(id,name,createdTime)",
            page_size=200,
            order_by="createdTime desc",
        ),
        headers={"Authorization": f"Bearer {token}", "Accept": "application/json"},
        summary_file=summary_file,
        context="drive-retention-list-manifests",
    )
    manifests = payload.get("files")
    if not isinstance(manifests, list):
        manifests = []
    if len(manifests) <= keep_count:
        _append_summary(summary_file, f"retention: no deletion needed (kept={len(manifests)}, limit={keep_count})")
        return {"deleted_files": [], "kept_manifests": len(manifests), "limit": keep_count}

    stale = manifests[keep_count:]
    deleted_files: list[dict[str, str]] = []
    for item in stale:
        if not isinstance(item, dict):
            continue
        name = str(item.get("name", "")).strip()
        if not name.endswith(".manifest.json"):
            continue
        stem = name[: -len(".manifest.json")]
        for related_name in (f"{stem}.tar.gz", f"{stem}.tar.gz.sha256", f"{stem}.manifest.json"):
            candidates = _find_files_by_name(
                token=token,
                folder_id=folder_id,
                name=related_name,
                summary_file=summary_file,
            )
            for candidate in candidates:
                candidate_id = candidate["id"]
                _delete_file(token=token, file_id=candidate_id, dry_run=dry_run, summary_file=summary_file)
                deleted_files.append(
                    {
                        "id_suffix": candidate_id[-8:],
                        "name": related_name,
                    }
                )
    _append_summary(
        summary_file,
        f"retention: deleted_files={len(deleted_files)} (manifest_limit={keep_count})",
    )
    return {"deleted_files": deleted_files, "kept_manifests": keep_count, "limit": keep_count}


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Upload release backup artifacts to Google Drive using OAuth refresh-token flow."
    )
    parser.add_argument("--artifact-path", required=True, help="Path to release archive (.tar.gz or .zip).")
    parser.add_argument("--tag", required=True, help="Release tag (example: v0.0.71).")
    parser.add_argument("--commit-sha", required=True, help="Commit SHA associated with release tag.")
    parser.add_argument("--folder-id", required=True, help="Google Drive folder ID target.")
    parser.add_argument("--oauth-client-id", required=True, help="OAuth Client ID.")
    parser.add_argument("--oauth-client-secret", required=True, help="OAuth Client Secret.")
    parser.add_argument("--oauth-refresh-token", required=True, help="OAuth refresh token.")
    parser.add_argument(
        "--artifact-prefix",
        default="spec-kit-release-backup",
        help="Artifact prefix used for retention matching.",
    )
    parser.add_argument(
        "--retention-count",
        type=int,
        default=30,
        help="How many backup sets to keep (based on manifest files).",
    )
    parser.add_argument("--release-published-at", default="", help="Release publication timestamp (UTC).")
    parser.add_argument("--summary-file", default="", help="Optional path to append timeline notes.")
    parser.add_argument("--repo", default=os.environ.get("GITHUB_REPOSITORY", ""), help="Repository slug.")
    parser.add_argument("--run-id", default=os.environ.get("GITHUB_RUN_ID", ""), help="GitHub run ID.")
    parser.add_argument(
        "--run-attempt", default=os.environ.get("GITHUB_RUN_ATTEMPT", ""), help="GitHub run attempt."
    )
    parser.add_argument("--dry-run", action="store_true", help="Do not call mutating Drive APIs.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    summary_file = Path(args.summary_file).resolve() if args.summary_file else None
    artifact_path = Path(args.artifact_path).resolve()
    folder_id = _normalize_folder_id(args.folder_id)
    _ensure_artifact(artifact_path)

    artifact_sha256 = _sha256_hex(artifact_path)
    checksum_name, manifest_name = _derive_names(artifact_path.name)
    checksum_path = artifact_path.parent / checksum_name
    manifest_path = artifact_path.parent / manifest_name
    _write_text(checksum_path, f"{artifact_sha256}  {artifact_path.name}\n")

    generated_at = _utc_now()
    manifest_payload: dict[str, Any] = {
        "artifact": {
            "name": artifact_path.name,
            "sha256": artifact_sha256,
            "size_bytes": artifact_path.stat().st_size,
        },
        "backup_kind": "release-source-archive",
        "commit_sha": args.commit_sha,
        "drive_target_folder_id": folder_id,
        "generated_at_utc": generated_at,
        "release_published_at": args.release_published_at or None,
        "repository": args.repo or None,
        "retention_count": args.retention_count,
        "run_attempt": args.run_attempt or None,
        "run_id": args.run_id or None,
        "tag": args.tag,
    }
    _write_json(manifest_path, manifest_payload)
    _append_summary(
        summary_file,
        (
            f"prepared artifacts: archive={artifact_path.name}, checksum={checksum_path.name}, "
            f"manifest={manifest_path.name}, size_bytes={artifact_path.stat().st_size}"
        ),
    )

    token, token_response = _refresh_access_token(
        client_id=args.oauth_client_id,
        client_secret=args.oauth_client_secret,
        refresh_token=args.oauth_refresh_token,
        summary_file=summary_file,
    )
    _append_summary(
        summary_file,
        (
            "oauth token refresh succeeded: "
            f"scope={token_response.get('scope', 'n/a')} "
            f"expires_in={token_response.get('expires_in', 'n/a')}"
        ),
    )
    _assert_folder_access(token=token, folder_id=folder_id, summary_file=summary_file)

    app_properties = {
        "backup_kind": "release-source-archive",
        "backup_tag": args.tag,
        "backup_commit": args.commit_sha,
        "backup_sha256": artifact_sha256,
        "backup_generated_at": generated_at,
    }

    uploads = [
        UploadArtifact(name=artifact_path.name, path=artifact_path, mime_type=_mime_for(artifact_path, "application/gzip")),
        UploadArtifact(name=checksum_path.name, path=checksum_path, mime_type="text/plain"),
        UploadArtifact(name=manifest_path.name, path=manifest_path, mime_type="application/json"),
    ]
    upload_results: list[dict[str, str]] = []
    for upload in uploads:
        upload_results.append(
            _upload_artifact(
                token=token,
                folder_id=folder_id,
                artifact=upload,
                app_properties=app_properties,
                dry_run=args.dry_run,
                summary_file=summary_file,
            )
        )

    retention = _apply_retention(
        token=token,
        folder_id=folder_id,
        keep_count=args.retention_count,
        prefix=args.artifact_prefix,
        dry_run=args.dry_run,
        summary_file=summary_file,
    )

    result = {
        "artifact_name": artifact_path.name,
        "artifact_sha256": artifact_sha256,
        "dry_run": args.dry_run,
        "manifest_name": manifest_path.name,
        "retention": retention,
        "tag": args.tag,
        "uploaded": upload_results,
    }
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except DriveBackupError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
