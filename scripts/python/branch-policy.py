#!/usr/bin/env python3
"""Canonical branch policy helper for feature execution units (issue #108)."""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


CONTRACT_VERSION = "branch-feature.v1"
FEATURE_BRANCH_PATTERN = re.compile(r"^(?P<prefix>\d{3})-(?P<slug>[a-z0-9]+(?:-[a-z0-9]+)*)$")


class BranchPolicyError(ValueError):
    """Raised when branch policy validation fails."""


@dataclass(frozen=True)
class ValidatedFeatureBranch:
    branch: str
    feature_prefix: str
    feature_id: str


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _as_repo_root(repo_root: str | Path) -> Path:
    raw_value = str(repo_root).strip() if repo_root is not None else ""
    if not raw_value:
        raise BranchPolicyError("Repository root must be a non-empty path.")
    path = Path(raw_value).expanduser().resolve()
    if not path.exists() or not path.is_dir():
        raise BranchPolicyError(f"Repository root does not exist: {path}")
    return path


def _contract_path(repo_root: Path) -> Path:
    return repo_root / ".spec-kit" / "branch-policy.json"


def validate_feature_branch(branch: str) -> ValidatedFeatureBranch:
    branch_name = (branch or "").strip()
    if not branch_name:
        raise BranchPolicyError("Branch must be a non-empty string.")
    match = FEATURE_BRANCH_PATTERN.fullmatch(branch_name)
    if not match:
        raise BranchPolicyError(
            "Branch must follow canonical feature branch pattern 'NNN-kebab-case' "
            "(example: 001-user-auth)."
        )

    return ValidatedFeatureBranch(
        branch=branch_name,
        feature_prefix=match.group("prefix"),
        feature_id=branch_name,
    )


def _default_contract() -> dict[str, Any]:
    now = _utc_now()
    return {
        "contract_version": CONTRACT_VERSION,
        "generated_by": "scripts/python/branch-policy.py",
        "updated_at": now,
        "entries": {},
    }


def _read_contract(repo_root: Path) -> dict[str, Any]:
    path = _contract_path(repo_root)
    if not path.exists():
        return _default_contract()

    try:
        raw_payload = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise BranchPolicyError(f"Unable to read branch policy contract at '{path}': {exc}") from exc

    try:
        payload = json.loads(raw_payload)
    except json.JSONDecodeError as exc:
        raise BranchPolicyError(f"Invalid branch policy JSON at '{path}': {exc}") from exc

    if not isinstance(payload, dict):
        raise BranchPolicyError("Branch policy contract must be a JSON object.")
    if payload.get("contract_version") != CONTRACT_VERSION:
        raise BranchPolicyError(
            f"Unsupported branch policy contract version: {payload.get('contract_version')!r}"
        )
    entries = payload.get("entries")
    if not isinstance(entries, dict):
        raise BranchPolicyError("Branch policy 'entries' must be a JSON object.")
    payload.setdefault("generated_by", "scripts/python/branch-policy.py")
    payload.setdefault("updated_at", _utc_now())
    return payload


def _write_contract(repo_root: Path, contract: dict[str, Any]) -> Path:
    contract_path = _contract_path(repo_root)
    contract_path.parent.mkdir(parents=True, exist_ok=True)
    contract["updated_at"] = _utc_now()
    temp_path = contract_path.with_suffix(".json.tmp")
    try:
        temp_path.write_text(json.dumps(contract, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        temp_path.replace(contract_path)
    except OSError as exc:
        try:
            if temp_path.exists():
                temp_path.unlink()
        except OSError:
            pass
        raise BranchPolicyError(f"Failed to write branch policy contract at '{contract_path}': {exc}") from exc
    return contract_path


def register_feature_branch(
    *,
    repo_root: str | Path,
    branch: str,
    feature_id: str,
    scope_mode: str = "feature",
    source_decision: str = "feature_mode",
) -> dict[str, Any]:
    root = _as_repo_root(repo_root)
    branch_info = validate_feature_branch(branch)
    feature_info = validate_feature_branch(feature_id)

    if scope_mode != "feature":
        raise BranchPolicyError("Branch policy registration currently supports scope_mode='feature' only.")

    if branch_info.feature_id != feature_info.feature_id:
        raise BranchPolicyError(
            "branch and feature_id must be identical for canonical one-branch-per-feature policy."
        )

    contract = _read_contract(root)
    entries: dict[str, Any] = contract["entries"]

    for existing_branch, existing_entry in entries.items():
        if not isinstance(existing_entry, dict):
            raise BranchPolicyError(f"Invalid contract entry format for branch '{existing_branch}'.")
        existing_prefix = str(existing_entry.get("feature_prefix", ""))
        existing_feature = str(existing_entry.get("feature_id", ""))
        if existing_prefix == branch_info.feature_prefix and existing_feature != feature_info.feature_id:
            raise BranchPolicyError(
                f"Feature prefix '{branch_info.feature_prefix}' is already assigned to '{existing_feature}'."
            )
        if existing_feature == feature_info.feature_id and existing_branch != branch_info.branch:
            raise BranchPolicyError(
                f"Feature '{feature_info.feature_id}' is already mapped to branch '{existing_branch}'."
            )

    now = _utc_now()
    previous = entries.get(branch_info.branch, {})
    created_at = previous.get("created_at", now) if isinstance(previous, dict) else now
    entries[branch_info.branch] = {
        "branch": branch_info.branch,
        "feature_id": feature_info.feature_id,
        "feature_prefix": branch_info.feature_prefix,
        "scope_mode": scope_mode,
        "source_decision": source_decision,
        "created_at": created_at,
        "updated_at": now,
    }
    contract_path = _write_contract(root, contract)
    return {
        "ok": True,
        "contract_path": str(contract_path),
        "entry": entries[branch_info.branch],
    }


def resolve_feature_dir(*, repo_root: str | Path, branch: str) -> dict[str, Any]:
    root = _as_repo_root(repo_root)
    branch_name = (branch or "").strip()
    if not branch_name:
        raise BranchPolicyError("Branch must be a non-empty string.")
    specs_dir = root / "specs"
    default_dir = specs_dir / branch_name

    if not specs_dir.exists() or not specs_dir.is_dir():
        return {
            "feature_dir": str(default_dir),
            "resolution": "default",
            "matches": [],
        }

    match = FEATURE_BRANCH_PATTERN.fullmatch(branch_name)
    if not match:
        return {
            "feature_dir": str(default_dir),
            "resolution": "default",
            "matches": [],
        }

    if default_dir.is_dir():
        return {
            "feature_dir": str(default_dir),
            "resolution": "exact",
            "matches": [branch_name],
        }

    prefix = match.group("prefix")
    matches = sorted(
        directory.name for directory in specs_dir.glob(f"{prefix}-*") if directory.is_dir()
    )

    if len(matches) == 1:
        return {
            "feature_dir": str(specs_dir / matches[0]),
            "resolution": "prefix",
            "matches": matches,
        }

    if len(matches) > 1:
        raise BranchPolicyError(
            f"Multiple spec directories found with prefix '{prefix}': {', '.join(matches)}"
        )

    return {
        "feature_dir": str(default_dir),
        "resolution": "default",
        "matches": [],
    }


def _cmd_validate(args: argparse.Namespace) -> int:
    validated = validate_feature_branch(args.branch)
    print(
        json.dumps(
            {
                "valid": True,
                "branch": validated.branch,
                "feature_prefix": validated.feature_prefix,
                "feature_id": validated.feature_id,
            }
        )
    )
    return 0


def _cmd_register_feature(args: argparse.Namespace) -> int:
    result = register_feature_branch(
        repo_root=args.repo_root,
        branch=args.branch,
        feature_id=args.feature_id,
        scope_mode=args.scope_mode,
        source_decision=args.source_decision,
    )
    print(json.dumps(result))
    return 0


def _cmd_resolve_feature_dir(args: argparse.Namespace) -> int:
    result = resolve_feature_dir(repo_root=args.repo_root, branch=args.branch)
    if args.path_only:
        print(result["feature_dir"])
    else:
        print(json.dumps(result))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Canonical feature branch policy helper.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    validate_parser = subparsers.add_parser("validate", help="Validate canonical feature branch naming.")
    validate_parser.add_argument("--branch", required=True, help="Branch to validate.")
    validate_parser.set_defaults(handler=_cmd_validate)

    register_parser = subparsers.add_parser(
        "register-feature", help="Register branch-feature metadata in .spec-kit/branch-policy.json."
    )
    register_parser.add_argument("--repo-root", required=True, help="Repository root path.")
    register_parser.add_argument("--branch", required=True, help="Canonical feature branch.")
    register_parser.add_argument("--feature-id", required=True, help="Canonical feature identifier.")
    register_parser.add_argument(
        "--scope-mode",
        default="feature",
        help="Scope mode for registration (currently feature only).",
    )
    register_parser.add_argument(
        "--source-decision",
        default="feature_mode",
        help="Origin of decision that produced this branch mapping.",
    )
    register_parser.set_defaults(handler=_cmd_register_feature)

    resolve_parser = subparsers.add_parser(
        "resolve-feature-dir", help="Resolve canonical feature directory for the active branch."
    )
    resolve_parser.add_argument("--repo-root", required=True, help="Repository root path.")
    resolve_parser.add_argument("--branch", required=True, help="Branch to resolve.")
    resolve_parser.add_argument(
        "--path-only",
        action="store_true",
        help="Return only the resolved feature directory path.",
    )
    resolve_parser.set_defaults(handler=_cmd_resolve_feature_dir)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return int(args.handler(args))
    except BranchPolicyError as exc:
        print(str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
