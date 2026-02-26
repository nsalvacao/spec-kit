"""Tests for canonical branch policy helper (issue #108)."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path


SCRIPT = Path(__file__).parent.parent / "scripts" / "python" / "branch-policy.py"


def run_policy(*args: str, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["python3", str(SCRIPT), *args],
        cwd=str(cwd) if cwd else None,
        capture_output=True,
        text=True,
    )


def test_validate_accepts_canonical_feature_branch() -> None:
    result = run_policy("validate", "--branch", "001-user-auth")

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["valid"] is True
    assert payload["feature_prefix"] == "001"
    assert payload["feature_id"] == "001-user-auth"


def test_validate_rejects_non_feature_branch_patterns() -> None:
    result = run_policy("validate", "--branch", "epic/identity")

    assert result.returncode != 0
    assert "canonical feature branch" in result.stderr.lower()


def test_register_feature_writes_contract_and_is_idempotent(tmp_path: Path) -> None:
    repo_root = tmp_path

    first = run_policy(
        "register-feature",
        "--repo-root",
        str(repo_root),
        "--branch",
        "002-payment-retry",
        "--feature-id",
        "002-payment-retry",
    )
    assert first.returncode == 0, first.stderr

    second = run_policy(
        "register-feature",
        "--repo-root",
        str(repo_root),
        "--branch",
        "002-payment-retry",
        "--feature-id",
        "002-payment-retry",
    )
    assert second.returncode == 0, second.stderr

    contract_path = repo_root / ".spec-kit" / "branch-policy.json"
    assert contract_path.exists()
    payload = json.loads(contract_path.read_text(encoding="utf-8"))
    assert payload["contract_version"] == "branch-feature.v1"
    assert payload["entries"]["002-payment-retry"]["feature_id"] == "002-payment-retry"
    assert payload["entries"]["002-payment-retry"]["feature_prefix"] == "002"


def test_register_feature_rejects_prefix_collision(tmp_path: Path) -> None:
    repo_root = tmp_path

    first = run_policy(
        "register-feature",
        "--repo-root",
        str(repo_root),
        "--branch",
        "003-user-auth",
        "--feature-id",
        "003-user-auth",
    )
    assert first.returncode == 0, first.stderr

    collision = run_policy(
        "register-feature",
        "--repo-root",
        str(repo_root),
        "--branch",
        "003-checkout-flow",
        "--feature-id",
        "003-checkout-flow",
    )
    assert collision.returncode != 0
    assert "prefix '003'" in collision.stderr.lower()


def test_resolve_feature_dir_uses_exact_and_prefix_lookup(tmp_path: Path) -> None:
    specs_dir = tmp_path / "specs"
    specs_dir.mkdir(parents=True)
    (specs_dir / "004-order-history").mkdir()

    exact = run_policy(
        "resolve-feature-dir",
        "--repo-root",
        str(tmp_path),
        "--branch",
        "004-order-history",
    )
    assert exact.returncode == 0, exact.stderr
    exact_payload = json.loads(exact.stdout)
    assert exact_payload["feature_dir"].endswith("specs/004-order-history")

    prefix = run_policy(
        "resolve-feature-dir",
        "--repo-root",
        str(tmp_path),
        "--branch",
        "004-branch-hotfix",
    )
    assert prefix.returncode == 0, prefix.stderr
    prefix_payload = json.loads(prefix.stdout)
    assert prefix_payload["feature_dir"].endswith("specs/004-order-history")


def test_resolve_feature_dir_fails_on_prefix_ambiguity(tmp_path: Path) -> None:
    specs_dir = tmp_path / "specs"
    specs_dir.mkdir(parents=True)
    (specs_dir / "005-a").mkdir()
    (specs_dir / "005-b").mkdir()

    result = run_policy(
        "resolve-feature-dir",
        "--repo-root",
        str(tmp_path),
        "--branch",
        "005-anything",
    )
    assert result.returncode != 0
    assert "multiple spec directories" in result.stderr.lower()
