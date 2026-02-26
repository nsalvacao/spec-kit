"""Tests for remote branch hygiene utility (issue #156)."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


SCRIPT = Path(__file__).parent.parent / "scripts" / "python" / "branch-hygiene.py"


def run_git(cwd: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=str(cwd),
        capture_output=True,
        text=True,
        check=False,
    )


def run_hygiene(repo_root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), "run", "--repo-root", str(repo_root), *args],
        cwd=str(repo_root),
        capture_output=True,
        text=True,
        check=False,
    )


def seed_policy(repo_root: Path) -> None:
    (repo_root / ".github").mkdir(parents=True, exist_ok=True)
    (repo_root / ".github" / "release-version-policy.yml").write_text(
        """policy_version: "1"
version:
  canonical_file: "pyproject.toml"
  canonical_pattern: '^version\\s*=\\s*"(?P<version>[0-9]+\\.[0-9]+\\.[0-9]+)"\\s*$'
changelog:
  file: "CHANGELOG.md"
  unreleased_heading: "## [Unreleased]"
  release_heading_pattern: '^## \\[(?P<version>[0-9]+\\.[0-9]+\\.[0-9]+)\\] - (?P<date>[0-9]{4}-[0-9]{2}-[0-9]{2})$'
branch_hygiene:
  protected_exact: ["main"]
  protected_prefixes: ["baseline/"]
sync:
  allowlist: ["pyproject.toml", "CHANGELOG.md"]
""",
        encoding="utf-8",
    )


def seed_git_repo(tmp_path: Path) -> Path:
    remote = tmp_path / "remote.git"
    local = tmp_path / "local"
    remote.mkdir(parents=True, exist_ok=True)
    local.mkdir(parents=True, exist_ok=True)

    assert run_git(remote, "init", "--bare").returncode == 0
    assert run_git(local, "init").returncode == 0
    assert run_git(local, "config", "user.email", "tester@example.com").returncode == 0
    assert run_git(local, "config", "user.name", "Tester").returncode == 0
    assert run_git(local, "remote", "add", "origin", str(remote)).returncode == 0

    (local / "README.md").write_text("# test\n", encoding="utf-8")
    assert run_git(local, "add", "README.md").returncode == 0
    assert run_git(local, "commit", "-m", "init").returncode == 0
    assert run_git(local, "branch", "-M", "main").returncode == 0
    assert run_git(local, "push", "-u", "origin", "main").returncode == 0

    # merged candidate branch
    assert run_git(local, "checkout", "-b", "001-merged-feature").returncode == 0
    (local / "merged.txt").write_text("merged\n", encoding="utf-8")
    assert run_git(local, "add", "merged.txt").returncode == 0
    assert run_git(local, "commit", "-m", "merged feature").returncode == 0
    assert run_git(local, "push", "-u", "origin", "001-merged-feature").returncode == 0
    assert run_git(local, "checkout", "main").returncode == 0
    assert run_git(local, "merge", "--no-ff", "001-merged-feature", "-m", "merge candidate").returncode == 0
    assert run_git(local, "push", "origin", "main").returncode == 0

    # non-merged branch
    assert run_git(local, "checkout", "-b", "002-open-feature").returncode == 0
    (local / "open.txt").write_text("open\n", encoding="utf-8")
    assert run_git(local, "add", "open.txt").returncode == 0
    assert run_git(local, "commit", "-m", "open feature").returncode == 0
    assert run_git(local, "push", "-u", "origin", "002-open-feature").returncode == 0
    assert run_git(local, "checkout", "main").returncode == 0

    seed_policy(local)
    return local


def test_branch_hygiene_lists_only_merged_non_protected_candidates(tmp_path: Path) -> None:
    repo = seed_git_repo(tmp_path)
    assert run_git(repo, "fetch", "origin", "--prune").returncode == 0

    result = run_hygiene(
        repo,
        "--policy",
        ".github/release-version-policy.yml",
        "--remote",
        "origin",
        "--json",
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["ok"] is True
    assert payload["apply"] is False
    assert "001-merged-feature" in payload["candidates"]
    assert "002-open-feature" in payload["skipped_not_merged"]
    assert "main" in payload["skipped_protected"]
    assert payload["deleted"] == []


def test_branch_hygiene_apply_deletes_merged_candidates(tmp_path: Path) -> None:
    repo = seed_git_repo(tmp_path)
    assert run_git(repo, "fetch", "origin", "--prune").returncode == 0

    result = run_hygiene(
        repo,
        "--policy",
        ".github/release-version-policy.yml",
        "--remote",
        "origin",
        "--apply",
        "--json",
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert "001-merged-feature" in payload["deleted"]

    refs = run_git(repo, "ls-remote", "--heads", "origin")
    assert refs.returncode == 0
    assert "refs/heads/001-merged-feature" not in refs.stdout
    assert "refs/heads/002-open-feature" in refs.stdout
