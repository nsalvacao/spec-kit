"""Tests for .gitignore security pattern bootstrap."""

from pathlib import Path

from specify_cli import ensure_gitignore_security


def test_ensure_gitignore_security_adds_local_config_pattern(tmp_path: Path):
    status = ensure_gitignore_security(tmp_path)
    assert status == "added"

    gitignore = tmp_path / ".gitignore"
    content = gitignore.read_text(encoding="utf-8")
    assert ".specify/spec-kit.local.yml" in content


def test_ensure_gitignore_security_is_idempotent(tmp_path: Path):
    first = ensure_gitignore_security(tmp_path)
    second = ensure_gitignore_security(tmp_path)
    assert first == "added"
    assert second == "already_configured"
