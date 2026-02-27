"""Tests for scripts/python/gdrive-release-backup.py."""

from __future__ import annotations

import importlib.util
from pathlib import Path
import sys

import pytest


REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT_PATH = REPO_ROOT / "scripts" / "python" / "gdrive-release-backup.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("gdrive_release_backup", SCRIPT_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


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
