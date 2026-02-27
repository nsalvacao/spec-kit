"""Regression tests for create-new-feature rollback behavior (issue #171)."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).parent.parent
BASH_CREATE_FEATURE = REPO_ROOT / "scripts" / "bash" / "create-new-feature.sh"
POWERSHELL_CREATE_FEATURE = REPO_ROOT / "scripts" / "powershell" / "create-new-feature.ps1"
PWSH = shutil.which("pwsh")
skip_no_pwsh = pytest.mark.skipif(PWSH is None, reason="pwsh not available")


def run_command(command: list[str], *, cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, cwd=str(cwd), capture_output=True, text=True)


def seed_git_repo_with_invalid_branch_policy(repo_root: Path) -> None:
    init_result = run_command(["git", "init", "-b", "main"], cwd=repo_root)
    if init_result.returncode != 0:
        fallback_init = run_command(["git", "init"], cwd=repo_root)
        assert fallback_init.returncode == 0, fallback_init.stderr
        rename_result = run_command(["git", "branch", "-M", "main"], cwd=repo_root)
        assert rename_result.returncode == 0, rename_result.stderr

    for command in (
        ["git", "config", "user.name", "Spec Kit Tests"],
        ["git", "config", "user.email", "spec-kit-tests@example.com"],
    ):
        result = run_command(command, cwd=repo_root)
        assert result.returncode == 0, result.stderr

    (repo_root / ".specify" / "templates").mkdir(parents=True, exist_ok=True)
    (repo_root / ".specify" / "templates" / "spec-template.md").write_text(
        "# Spec template\n", encoding="utf-8"
    )
    (repo_root / ".spec-kit").mkdir(parents=True, exist_ok=True)
    (repo_root / ".spec-kit" / "branch-policy.json").write_text("{invalid-json", encoding="utf-8")
    (repo_root / "README.md").write_text("test repo\n", encoding="utf-8")

    add_result = run_command(["git", "add", "."], cwd=repo_root)
    assert add_result.returncode == 0, add_result.stderr
    commit_result = run_command(["git", "commit", "-m", "seed repo"], cwd=repo_root)
    assert commit_result.returncode == 0, commit_result.stderr


def assert_feature_branch_rollback(repo_root: Path, branch_name: str) -> None:
    feature_dir = repo_root / "specs" / branch_name
    assert not feature_dir.exists(), "Feature directory should be removed after rollback."

    current_branch = run_command(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=repo_root)
    assert current_branch.returncode == 0, current_branch.stderr
    assert current_branch.stdout.strip() == "main"

    branch_lookup = run_command(["git", "branch", "--list", branch_name], cwd=repo_root)
    assert branch_lookup.returncode == 0, branch_lookup.stderr
    assert branch_lookup.stdout.strip() == ""


def test_bash_create_feature_rolls_back_when_branch_policy_registration_fails(tmp_path: Path) -> None:
    seed_git_repo_with_invalid_branch_policy(tmp_path)

    result = run_command(
        [
            "bash",
            str(BASH_CREATE_FEATURE),
            "--short-name",
            "rollback-test",
            "Add rollback coverage",
        ],
        cwd=tmp_path,
    )

    combined_output = f"{result.stdout}\n{result.stderr}".lower()
    assert result.returncode != 0, combined_output
    assert "failed to register canonical branch metadata" in combined_output

    assert_feature_branch_rollback(tmp_path, "001-rollback-test")


@skip_no_pwsh
def test_powershell_create_feature_rolls_back_when_branch_policy_registration_fails(tmp_path: Path) -> None:
    seed_git_repo_with_invalid_branch_policy(tmp_path)

    result = run_command(
        [
            PWSH,
            "-NoProfile",
            "-NonInteractive",
            "-File",
            str(POWERSHELL_CREATE_FEATURE),
            "-ShortName",
            "rollback-test",
            "-FeatureDescription",
            "Add rollback coverage",
        ],
        cwd=tmp_path,
    )

    combined_output = f"{result.stdout}\n{result.stderr}".lower()
    assert result.returncode != 0, combined_output
    assert "failed to register canonical branch metadata" in combined_output

    assert_feature_branch_rollback(tmp_path, "001-rollback-test")
