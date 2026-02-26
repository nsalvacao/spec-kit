#!/usr/bin/env python3
"""Remote branch hygiene utility (issue #156)."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


class BranchHygieneError(ValueError):
    """Raised when branch hygiene processing fails."""


@dataclass(frozen=True)
class HygienePolicy:
    protected_exact: tuple[str, ...]
    protected_prefixes: tuple[str, ...]


def _run_git(repo_root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=str(repo_root),
        capture_output=True,
        text=True,
        check=False,
    )


def _as_repo_root(repo_root: str | Path) -> Path:
    raw = str(repo_root).strip() if repo_root is not None else ""
    if not raw:
        raise BranchHygieneError("Repository root must be a non-empty path.")
    root = Path(raw).expanduser().resolve()
    if not root.exists() or not root.is_dir():
        raise BranchHygieneError(f"Repository root does not exist: {root}")
    probe = _run_git(root, "rev-parse", "--show-toplevel")
    if probe.returncode != 0:
        raise BranchHygieneError("Repository root is not a git repository.")
    return root


def _load_policy(repo_root: Path, policy_path: str | Path) -> HygienePolicy:
    path = Path(str(policy_path).strip())
    if not path.is_absolute():
        path = repo_root / path
    path = path.resolve()
    if not path.exists() or not path.is_file():
        raise BranchHygieneError(f"Policy file not found: {path}")

    try:
        payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError as exc:
        raise BranchHygieneError(f"Invalid YAML policy file '{path}': {exc}") from exc

    branch_cfg = payload.get("branch_hygiene") or {}
    if not isinstance(branch_cfg, dict):
        raise BranchHygieneError("Policy 'branch_hygiene' section must be a mapping.")

    protected_exact = branch_cfg.get("protected_exact") or []
    protected_prefixes = branch_cfg.get("protected_prefixes") or []
    if not isinstance(protected_exact, list) or any(not isinstance(item, str) for item in protected_exact):
        raise BranchHygieneError("Policy 'branch_hygiene.protected_exact' must be a list of strings.")
    if not isinstance(protected_prefixes, list) or any(
        not isinstance(item, str) for item in protected_prefixes
    ):
        raise BranchHygieneError("Policy 'branch_hygiene.protected_prefixes' must be a list of strings.")

    return HygienePolicy(
        protected_exact=tuple(sorted(set(item.strip() for item in protected_exact if item.strip()))),
        protected_prefixes=tuple(sorted(set(item.strip() for item in protected_prefixes if item.strip()))),
    )


def _is_protected(branch: str, policy: HygienePolicy) -> bool:
    if branch in policy.protected_exact:
        return True
    for prefix in policy.protected_prefixes:
        if branch.startswith(prefix):
            return True
    return False


def _remote_branches(repo_root: Path, remote: str) -> list[str]:
    result = _run_git(
        repo_root,
        "for-each-ref",
        "--format=%(refname:short)",
        f"refs/remotes/{remote}",
    )
    if result.returncode != 0:
        raise BranchHygieneError(result.stderr.strip() or "Failed to list remote branches.")

    branches: list[str] = []
    for raw in result.stdout.splitlines():
        ref = raw.strip()
        if not ref or ref == f"{remote}/HEAD":
            continue
        if not ref.startswith(f"{remote}/"):
            continue
        branches.append(ref.split("/", 1)[1])
    return sorted(set(branches))


def _is_merged_into_main(repo_root: Path, remote: str, branch: str) -> bool:
    probe = _run_git(repo_root, "merge-base", "--is-ancestor", f"{remote}/{branch}", f"{remote}/main")
    return probe.returncode == 0


def run_branch_hygiene(
    *,
    repo_root: Path,
    policy: HygienePolicy,
    remote: str,
    apply: bool,
) -> dict[str, Any]:
    remote_url = _run_git(repo_root, "remote", "get-url", remote)
    if remote_url.returncode != 0:
        raise BranchHygieneError(f"Remote '{remote}' not found.")

    branches = _remote_branches(repo_root, remote)
    candidates: list[str] = []
    skipped_protected: list[str] = []
    skipped_not_merged: list[str] = []

    for branch in branches:
        if _is_protected(branch, policy):
            skipped_protected.append(branch)
            continue
        if _is_merged_into_main(repo_root, remote, branch):
            candidates.append(branch)
        else:
            skipped_not_merged.append(branch)

    deleted: list[str] = []
    failed: dict[str, str] = {}
    if apply:
        for branch in candidates:
            deletion = _run_git(repo_root, "push", remote, "--delete", branch)
            if deletion.returncode == 0:
                deleted.append(branch)
            else:
                failed[branch] = (deletion.stderr or deletion.stdout or "unknown delete failure").strip()

    return {
        "ok": len(failed) == 0,
        "remote": remote,
        "apply": apply,
        "protected_exact": list(policy.protected_exact),
        "protected_prefixes": list(policy.protected_prefixes),
        "candidates": candidates,
        "deleted": deleted,
        "failed": failed,
        "skipped_protected": skipped_protected,
        "skipped_not_merged": skipped_not_merged,
    }


def _cmd_run(args: argparse.Namespace) -> int:
    root = _as_repo_root(args.repo_root)
    policy = _load_policy(root, args.policy)
    payload = run_branch_hygiene(
        repo_root=root,
        policy=policy,
        remote=args.remote,
        apply=args.apply,
    )
    if args.json:
        print(json.dumps(payload))
    else:
        print(json.dumps(payload, indent=2))
    return 0 if payload["ok"] else 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Remote branch hygiene helper.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_parser = subparsers.add_parser("run", help="List/delete merged remote branches using policy.")
    run_parser.add_argument("--repo-root", default=".", help="Repository root path.")
    run_parser.add_argument(
        "--policy",
        default=".github/release-version-policy.yml",
        help="Branch hygiene policy file.",
    )
    run_parser.add_argument("--remote", default="origin", help="Remote name (default: origin).")
    run_parser.add_argument("--apply", action="store_true", help="Delete candidate branches from remote.")
    run_parser.add_argument("--json", action="store_true", help="Emit compact JSON output.")
    run_parser.set_defaults(handler=_cmd_run)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return int(args.handler(args))
    except BranchHygieneError as exc:
        print(str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
