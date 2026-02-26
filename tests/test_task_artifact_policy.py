"""Tests for canonical tasks artifact policy validator (issue #109)."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


SCRIPT = Path(__file__).parent.parent / "scripts" / "python" / "task-artifact-policy.py"


def run_policy(*args: str, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        cwd=str(cwd) if cwd else None,
        capture_output=True,
        text=True,
    )


def test_validate_accepts_canonical_tasks_artifact_layout(tmp_path: Path) -> None:
    feature_dir = tmp_path / "specs" / "001-user-auth"
    feature_dir.mkdir(parents=True)

    result = run_policy(
        "validate",
        "--repo-root",
        str(tmp_path),
        "--feature-dir",
        str(feature_dir),
        "--tasks-path",
        str(feature_dir / "tasks.md"),
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["ok"] is True
    assert payload["policy"] == "single-canonical-tasks-artifact.v1"


def test_validate_rejects_non_canonical_tasks_path(tmp_path: Path) -> None:
    feature_dir = tmp_path / "specs" / "002-payment-retry"
    feature_dir.mkdir(parents=True)

    result = run_policy(
        "validate",
        "--repo-root",
        str(tmp_path),
        "--feature-dir",
        str(feature_dir),
        "--tasks-path",
        str(tmp_path / "tasks.md"),
    )

    assert result.returncode != 0
    assert "canonical path" in result.stderr.lower()


def test_validate_rejects_duplicate_tasks_prefix_collision(tmp_path: Path) -> None:
    feature_a = tmp_path / "specs" / "003-user-auth"
    feature_b = tmp_path / "specs" / "003-checkout-flow"
    feature_a.mkdir(parents=True)
    feature_b.mkdir(parents=True)
    (feature_a / "tasks.md").write_text("# tasks a\n", encoding="utf-8")
    (feature_b / "tasks.md").write_text("# tasks b\n", encoding="utf-8")

    result = run_policy(
        "validate",
        "--repo-root",
        str(tmp_path),
        "--feature-dir",
        str(feature_a),
        "--tasks-path",
        str(feature_a / "tasks.md"),
    )

    assert result.returncode != 0
    assert "duplicate tasks artifacts" in result.stderr.lower()
    assert "003" in result.stderr


def test_validate_rejects_root_monolithic_tasks_for_multi_feature_repo(tmp_path: Path) -> None:
    feature_a = tmp_path / "specs" / "004-orders"
    feature_b = tmp_path / "specs" / "005-payments"
    feature_a.mkdir(parents=True)
    feature_b.mkdir(parents=True)
    (tmp_path / "tasks.md").write_text("# monolithic tasks\n", encoding="utf-8")

    result = run_policy(
        "validate",
        "--repo-root",
        str(tmp_path),
        "--feature-dir",
        str(feature_a),
        "--tasks-path",
        str(feature_a / "tasks.md"),
    )

    assert result.returncode != 0
    assert "forbidden root-level 'tasks.md'" in result.stderr.lower()


def test_validate_allows_root_tasks_when_only_one_feature_exists(tmp_path: Path) -> None:
    feature_dir = tmp_path / "specs" / "006-observability"
    feature_dir.mkdir(parents=True)
    (tmp_path / "tasks.md").write_text("# legacy tasks\n", encoding="utf-8")

    result = run_policy(
        "validate",
        "--repo-root",
        str(tmp_path),
        "--feature-dir",
        str(feature_dir),
        "--tasks-path",
        str(feature_dir / "tasks.md"),
    )

    assert result.returncode == 0, result.stderr


def test_validate_rejects_illegal_nested_tasks_paths(tmp_path: Path) -> None:
    feature_dir = tmp_path / "specs" / "007-api-gateway"
    nested_tasks_dir = feature_dir / "subscope"
    nested_tasks_dir.mkdir(parents=True)
    (nested_tasks_dir / "tasks.md").write_text("# nested tasks\n", encoding="utf-8")

    result = run_policy(
        "validate",
        "--repo-root",
        str(tmp_path),
        "--feature-dir",
        str(feature_dir),
        "--tasks-path",
        str(feature_dir / "tasks.md"),
    )

    assert result.returncode != 0
    assert "outside canonical path" in result.stderr.lower()
