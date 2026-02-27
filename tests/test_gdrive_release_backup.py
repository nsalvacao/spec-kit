"""Tests for scripts/python/gdrive-release-backup.py."""

from __future__ import annotations

from pathlib import Path
import runpy
from types import SimpleNamespace

import pytest


REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT_PATH = REPO_ROOT / "scripts" / "python" / "gdrive-release-backup.py"


def _load_module():
    namespace = runpy.run_path(str(SCRIPT_PATH), run_name="__spec_kit_gdrive_backup_test__")
    return SimpleNamespace(**namespace)


mod = _load_module()


def test_derive_names_for_tar_gz():
    checksum, manifest = mod._derive_names("spec-kit-release-backup-v0.0.71.tar.gz")
    assert checksum == "spec-kit-release-backup-v0.0.71.tar.gz.sha256"
    assert manifest == "spec-kit-release-backup-v0.0.71.manifest.json"


def test_extract_retry_after_prefers_header():
    retry_after = mod._extract_retry_after({"Retry-After": "7"}, {"retry_after": 3})
    assert retry_after == 7


def test_extract_retry_after_from_body_retry_after_string():
    retry_after = mod._extract_retry_after({}, {"retry_after": "11"})
    assert retry_after == 11


def test_extract_retry_after_from_body_error_details():
    retry_after = mod._extract_retry_after(
        {},
        {"error": {"details": [{"retryDelay": "9s"}]}},
    )
    assert retry_after == 9


def test_read_json_bytes_non_mapping_returns_empty():
    assert mod._read_json_bytes(b'["not","a","mapping"]') == {}


def test_sha256_hex(tmp_path: Path):
    target = tmp_path / "artifact.tar.gz"
    target.write_bytes(b"spec-kit-backup")
    digest = mod._sha256_hex(target)
    assert len(digest) == 64
    assert all(char in "0123456789abcdef" for char in digest)


def test_ensure_artifact_rejects_missing(tmp_path: Path):
    with pytest.raises(mod.DriveBackupError, match="artifact does not exist"):
        mod._ensure_artifact(tmp_path / "missing.tar.gz")


def test_ensure_artifact_rejects_empty(tmp_path: Path):
    target = tmp_path / "empty.tar.gz"
    target.write_bytes(b"")
    with pytest.raises(mod.DriveBackupError, match="artifact is empty"):
        mod._ensure_artifact(target)


def test_normalize_folder_id_rejects_quote_injection():
    with pytest.raises(mod.DriveBackupError, match="folder id is invalid"):
        mod._normalize_folder_id("1Vo5am-0R2hjeWn' or trashed=true")


def test_normalize_folder_id_accepts_valid_identifier():
    resolved = mod._normalize_folder_id("1Vo5am-0R2hjeWnjC2YABmVCM_EwCTITm")
    assert resolved == "1Vo5am-0R2hjeWnjC2YABmVCM_EwCTITm"


def test_escape_drive_query_literal_escapes_single_quote():
    escaped = mod._escape_drive_query_literal("abc'def")
    assert escaped == "abc\\'def"


def test_redact_sensitive_text_masks_known_keys():
    sample = 'error={"refresh_token":"abc123","client_secret":"xyz"}?access_token=qwerty'
    redacted = mod._redact_sensitive_text(sample)
    assert "abc123" not in redacted
    assert "xyz" not in redacted
    assert "qwerty" not in redacted


def test_multipart_body_rejects_oversized_artifact(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    artifact = tmp_path / "big.tar.gz"
    artifact.write_bytes(b"0123456789")
    monkeypatch.setitem(mod._multipart_body.__globals__, "MAX_MULTIPART_UPLOAD_BYTES", 4)
    with pytest.raises(mod.DriveBackupError, match="too large for multipart upload buffer"):
        mod._multipart_body({"name": "big.tar.gz"}, artifact, "application/gzip")


def test_require_non_empty_rejects_blank_values():
    with pytest.raises(mod.DriveBackupError, match="oauth client id is required"):
        mod._require_non_empty("   ", field_name="oauth client id")


def test_parser_reads_oauth_from_environment(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    artifact = tmp_path / "artifact.tar.gz"
    artifact.write_bytes(b"ok")
    monkeypatch.setenv("GDRIVE_OAUTH_CLIENT_ID", "client-id-env")
    monkeypatch.setenv("GDRIVE_OAUTH_CLIENT_SECRET", "client-secret-env")
    monkeypatch.setenv("GDRIVE_OAUTH_REFRESH_TOKEN", "refresh-token-env")

    parser = mod._build_parser()
    args = parser.parse_args(
        [
            "--artifact-path",
            str(artifact),
            "--tag",
            "v0.0.1",
            "--commit-sha",
            "0123456789abcdef",
            "--folder-id",
            "1Vo5am-0R2hjeWnjC2YABmVCM_EwCTITm",
        ]
    )

    assert args.oauth_client_id == "client-id-env"
    assert args.oauth_client_secret == "client-secret-env"
    assert args.oauth_refresh_token == "refresh-token-env"
