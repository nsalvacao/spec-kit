"""Tests for canonical branch policy helper (issue #108)."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


SCRIPT = Path(__file__).parent.parent / "scripts" / "python" / "branch-policy.py"


def run_policy(*args: str, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
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


def test_register_feature_supports_optional_parent_lineage_fields(tmp_path: Path) -> None:
    result = run_policy(
        "register-feature",
        "--repo-root",
        str(tmp_path),
        "--branch",
        "006-account-settings",
        "--feature-id",
        "006-account-settings",
        "--parent-epic-id",
        "epic-authentication",
        "--parent-program-id",
        "program-core-platform",
    )
    assert result.returncode == 0, result.stderr

    payload = json.loads((tmp_path / ".spec-kit" / "branch-policy.json").read_text(encoding="utf-8"))
    entry = payload["entries"]["006-account-settings"]
    assert entry["parent_epic_id"] == "epic-authentication"
    assert entry["parent_program_id"] == "program-core-platform"


def test_register_feature_rejects_non_feature_scope_mode(tmp_path: Path) -> None:
    result = run_policy(
        "register-feature",
        "--repo-root",
        str(tmp_path),
        "--branch",
        "011-canonical-unit",
        "--feature-id",
        "011-canonical-unit",
        "--scope-mode",
        "epic",
    )

    assert result.returncode != 0
    assert "scope_mode='feature' only" in result.stderr


def test_register_feature_preserves_existing_parent_lineage_when_re_registering(tmp_path: Path) -> None:
    first = run_policy(
        "register-feature",
        "--repo-root",
        str(tmp_path),
        "--branch",
        "007-feature-flags",
        "--feature-id",
        "007-feature-flags",
        "--parent-epic-id",
        "epic-rollout",
        "--parent-program-id",
        "program-foundation",
    )
    assert first.returncode == 0, first.stderr

    second = run_policy(
        "register-feature",
        "--repo-root",
        str(tmp_path),
        "--branch",
        "007-feature-flags",
        "--feature-id",
        "007-feature-flags",
    )
    assert second.returncode == 0, second.stderr

    payload = json.loads((tmp_path / ".spec-kit" / "branch-policy.json").read_text(encoding="utf-8"))
    entry = payload["entries"]["007-feature-flags"]
    assert entry["parent_epic_id"] == "epic-rollout"
    assert entry["parent_program_id"] == "program-foundation"


def test_register_feature_repairs_legacy_contract_entries_missing_identity_fields(tmp_path: Path) -> None:
    policy_dir = tmp_path / ".spec-kit"
    policy_dir.mkdir(parents=True)
    (policy_dir / "branch-policy.json").write_text(
        json.dumps(
            {
                "contract_version": "branch-feature.v1",
                "generated_by": "tests",
                "updated_at": "2026-02-27T12:00:00Z",
                "entries": {
                    "009-legacy-metadata": {
                        "scope_mode": "feature",
                        "source_decision": "legacy",
                        "parent_epic_id": None,
                        "created_at": "2026-02-27T12:00:00Z",
                        "updated_at": "2026-02-27T12:00:00Z",
                    }
                },
            }
        ),
        encoding="utf-8",
    )

    result = run_policy(
        "register-feature",
        "--repo-root",
        str(tmp_path),
        "--branch",
        "009-legacy-metadata",
        "--feature-id",
        "009-legacy-metadata",
    )
    assert result.returncode == 0, result.stderr

    payload = json.loads((tmp_path / ".spec-kit" / "branch-policy.json").read_text(encoding="utf-8"))
    entry = payload["entries"]["009-legacy-metadata"]
    assert entry["branch"] == "009-legacy-metadata"
    assert entry["feature_id"] == "009-legacy-metadata"
    assert entry["feature_prefix"] == "009"
    assert "parent_epic_id" not in entry


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


def test_resolve_feature_dir_fails_on_metadata_branch_inconsistency(tmp_path: Path) -> None:
    policy_dir = tmp_path / ".spec-kit"
    policy_dir.mkdir(parents=True)
    (policy_dir / "branch-policy.json").write_text(
        json.dumps(
            {
                "contract_version": "branch-feature.v1",
                "generated_by": "tests",
                "updated_at": "2026-02-27T12:00:00Z",
                "entries": {
                    "008-canonical-feature": {
                        "branch": "008-canonical-feature",
                        "feature_id": "999-other-feature",
                        "feature_prefix": "008",
                        "scope_mode": "feature",
                        "source_decision": "feature_mode",
                        "created_at": "2026-02-27T12:00:00Z",
                        "updated_at": "2026-02-27T12:00:00Z",
                    }
                },
            }
        ),
        encoding="utf-8",
    )

    result = run_policy(
        "resolve-feature-dir",
        "--repo-root",
        str(tmp_path),
        "--branch",
        "008-canonical-feature",
    )
    assert result.returncode != 0
    assert "inconsistent branch policy entry" in result.stderr.lower()


def test_validate_rejects_empty_branch_argument() -> None:
    result = run_policy("validate", "--branch", "")

    assert result.returncode != 0
    assert "non-empty string" in result.stderr.lower()


def test_register_feature_rejects_empty_repo_root() -> None:
    result = run_policy(
        "register-feature",
        "--repo-root",
        "",
        "--branch",
        "010-api-gateway",
        "--feature-id",
        "010-api-gateway",
    )

    assert result.returncode != 0
    assert "non-empty path" in result.stderr.lower()
