#!/usr/bin/env python3
"""Canonical tasks artifact policy validator (issue #109)."""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from pathlib import Path


FEATURE_DIR_PATTERN = re.compile(r"^(?P<prefix>\d{3})-[a-z0-9]+(?:-[a-z0-9]+)*$")


class TaskArtifactPolicyError(ValueError):
    """Raised when tasks artifact policy validation fails."""


def _as_path(value: str | Path | None, *, field_name: str) -> Path:
    raw_value = str(value).strip() if value is not None else ""
    if not raw_value:
        raise TaskArtifactPolicyError(f"{field_name} must be a non-empty path.")
    return Path(raw_value).expanduser().resolve()


def _as_repo_root(repo_root: str | Path) -> Path:
    path = _as_path(repo_root, field_name="Repository root")
    if not path.exists() or not path.is_dir():
        raise TaskArtifactPolicyError(f"Repository root does not exist: {path}")
    return path


def _normalize_feature_dir(repo_root: Path, feature_dir: str | Path) -> Path:
    path = _as_path(feature_dir, field_name="Feature directory")
    if not path.exists() or not path.is_dir():
        raise TaskArtifactPolicyError(f"Feature directory does not exist: {path}")

    try:
        relative = path.relative_to(repo_root)
    except ValueError as exc:
        raise TaskArtifactPolicyError(
            f"Feature directory must be inside repository root: {path}"
        ) from exc

    if len(relative.parts) != 2 or relative.parts[0] != "specs":
        raise TaskArtifactPolicyError(
            "Feature directory must follow canonical path 'specs/<feature-id>'."
        )

    feature_id = relative.parts[1]
    if FEATURE_DIR_PATTERN.fullmatch(feature_id) is None:
        raise TaskArtifactPolicyError(
            "Feature directory must match canonical id pattern 'NNN-kebab-case'."
        )
    return path


def _normalize_tasks_path(tasks_path: str | Path, *, expected_path: Path) -> Path:
    path = _as_path(tasks_path, field_name="Tasks path")
    if path != expected_path:
        raise TaskArtifactPolicyError(
            f"tasks.md must be written only to canonical path: {expected_path}"
        )
    return path


def _collect_canonical_feature_dirs(repo_root: Path) -> list[Path]:
    specs_dir = repo_root / "specs"
    if not specs_dir.exists() or not specs_dir.is_dir():
        return []

    feature_dirs: list[Path] = []
    for child in sorted(specs_dir.iterdir()):
        if child.is_dir() and FEATURE_DIR_PATTERN.fullmatch(child.name):
            feature_dirs.append(child)
    return feature_dirs


def _assert_no_duplicate_prefix_tasks(feature_dirs: list[Path]) -> None:
    by_prefix: dict[str, list[str]] = defaultdict(list)
    for feature_dir in feature_dirs:
        tasks_path = feature_dir / "tasks.md"
        if tasks_path.is_file():
            prefix = feature_dir.name.split("-", 1)[0]
            by_prefix[prefix].append(feature_dir.name)

    collisions = {prefix: sorted(names) for prefix, names in by_prefix.items() if len(names) > 1}
    if collisions:
        collision_text = "; ".join(
            f"{prefix}: {', '.join(names)}" for prefix, names in sorted(collisions.items())
        )
        raise TaskArtifactPolicyError(
            "Duplicate tasks artifacts detected for the same feature prefix. "
            f"Resolve to a single canonical feature directory per prefix. Collisions: {collision_text}"
        )


def _assert_no_illegal_tasks_paths(repo_root: Path) -> None:
    specs_dir = repo_root / "specs"
    if not specs_dir.exists() or not specs_dir.is_dir():
        return

    illegal_paths: list[str] = []
    for tasks_file in specs_dir.rglob("tasks.md"):
        relative_parts = tasks_file.relative_to(specs_dir).parts
        is_canonical = (
            len(relative_parts) == 2
            and relative_parts[1] == "tasks.md"
            and FEATURE_DIR_PATTERN.fullmatch(relative_parts[0]) is not None
        )
        if not is_canonical:
            illegal_paths.append(tasks_file.relative_to(repo_root).as_posix())

    if illegal_paths:
        listed = ", ".join(sorted(illegal_paths))
        raise TaskArtifactPolicyError(
            "Found tasks.md outside canonical path 'specs/<feature>/tasks.md'. "
            f"Illegal paths: {listed}"
        )


def _assert_no_root_monolithic_tasks(repo_root: Path, *, feature_count: int) -> None:
    root_tasks = repo_root / "tasks.md"
    if root_tasks.is_file() and feature_count >= 2:
        raise TaskArtifactPolicyError(
            "Found forbidden root-level 'tasks.md' while multiple features exist. "
            "Move each task list to 'specs/<feature>/tasks.md' and delete the root monolith."
        )


def validate_tasks_policy(
    *,
    repo_root: str | Path,
    feature_dir: str | Path,
    tasks_path: str | Path,
) -> dict[str, object]:
    root = _as_repo_root(repo_root)
    normalized_feature_dir = _normalize_feature_dir(root, feature_dir)
    canonical_tasks_path = normalized_feature_dir / "tasks.md"
    normalized_tasks_path = _normalize_tasks_path(tasks_path, expected_path=canonical_tasks_path)

    feature_dirs = _collect_canonical_feature_dirs(root)
    _assert_no_duplicate_prefix_tasks(feature_dirs)
    _assert_no_illegal_tasks_paths(root)
    _assert_no_root_monolithic_tasks(root, feature_count=len(feature_dirs))

    return {
        "ok": True,
        "repo_root": str(root),
        "feature_dir": str(normalized_feature_dir),
        "tasks_path": str(normalized_tasks_path),
        "feature_count": len(feature_dirs),
        "policy": "single-canonical-tasks-artifact.v1",
    }


def _cmd_validate(args: argparse.Namespace) -> int:
    payload = validate_tasks_policy(
        repo_root=args.repo_root,
        feature_dir=args.feature_dir,
        tasks_path=args.tasks_path,
    )
    print(json.dumps(payload))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate canonical tasks artifact policy for specs/<feature>/tasks.md."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    validate_parser = subparsers.add_parser("validate", help="Validate canonical tasks artifact policy.")
    validate_parser.add_argument("--repo-root", required=True, help="Repository root path.")
    validate_parser.add_argument("--feature-dir", required=True, help="Resolved canonical feature directory path.")
    validate_parser.add_argument("--tasks-path", required=True, help="Resolved tasks.md path.")
    validate_parser.set_defaults(handler=_cmd_validate)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return int(args.handler(args))
    except TaskArtifactPolicyError as exc:
        print(str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
