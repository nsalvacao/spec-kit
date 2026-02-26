#!/usr/bin/env python3
"""Release metadata consistency checks and synchronization (issue #156)."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

import yaml


TAG_PATTERN = re.compile(r"^v(?P<version>[0-9]+\.[0-9]+\.[0-9]+(?:-fork\.[0-9]+)?)$")


class ReleaseMetadataError(ValueError):
    """Raised when release metadata validation fails."""


@dataclass(frozen=True)
class Policy:
    canonical_file: str
    canonical_pattern: str
    changelog_file: str
    unreleased_heading: str
    release_heading_pattern: str
    sync_allowlist: tuple[str, ...]


def _as_repo_root(repo_root: str | Path) -> Path:
    raw = str(repo_root).strip() if repo_root is not None else ""
    if not raw:
        raise ReleaseMetadataError("Repository root must be a non-empty path.")
    root = Path(raw).expanduser().resolve()
    if not root.exists() or not root.is_dir():
        raise ReleaseMetadataError(f"Repository root does not exist: {root}")
    return root


def _load_policy(repo_root: Path, policy_path: str | Path) -> Policy:
    raw = str(policy_path).strip() if policy_path is not None else ""
    if not raw:
        raise ReleaseMetadataError("Policy path must be a non-empty path.")
    path = Path(raw)
    if not path.is_absolute():
        path = repo_root / path
    path = path.resolve()
    if not path.exists() or not path.is_file():
        raise ReleaseMetadataError(f"Policy file not found: {path}")

    try:
        payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError as exc:
        raise ReleaseMetadataError(f"Invalid YAML policy file '{path}': {exc}") from exc

    if not isinstance(payload, dict):
        raise ReleaseMetadataError("Policy root must be a mapping.")

    version_cfg = payload.get("version") or {}
    changelog_cfg = payload.get("changelog") or {}
    sync_cfg = payload.get("sync") or {}
    allowlist = sync_cfg.get("allowlist") or []

    if not isinstance(version_cfg, dict):
        raise ReleaseMetadataError("Policy 'version' section must be a mapping.")
    if not isinstance(changelog_cfg, dict):
        raise ReleaseMetadataError("Policy 'changelog' section must be a mapping.")
    if not isinstance(allowlist, list) or any(not isinstance(item, str) for item in allowlist):
        raise ReleaseMetadataError("Policy 'sync.allowlist' must be a list of strings.")

    canonical_file = str(version_cfg.get("canonical_file", "")).strip()
    canonical_pattern = str(version_cfg.get("canonical_pattern", "")).strip()
    changelog_file = str(changelog_cfg.get("file", "")).strip()
    unreleased_heading = str(changelog_cfg.get("unreleased_heading", "")).strip()
    release_heading_pattern = str(changelog_cfg.get("release_heading_pattern", "")).strip()

    required_fields = {
        "version.canonical_file": canonical_file,
        "version.canonical_pattern": canonical_pattern,
        "changelog.file": changelog_file,
        "changelog.unreleased_heading": unreleased_heading,
        "changelog.release_heading_pattern": release_heading_pattern,
    }
    missing = [field for field, value in required_fields.items() if not value]
    if missing:
        raise ReleaseMetadataError(f"Policy missing required fields: {', '.join(missing)}")

    return Policy(
        canonical_file=canonical_file,
        canonical_pattern=canonical_pattern,
        changelog_file=changelog_file,
        unreleased_heading=unreleased_heading,
        release_heading_pattern=release_heading_pattern,
        sync_allowlist=tuple(sorted(set(allowlist))),
    )


def _normalize_release_tag(release_tag: str) -> str:
    tag = (release_tag or "").strip()
    if not tag:
        raise ReleaseMetadataError("Release tag must be a non-empty string.")
    match = TAG_PATTERN.fullmatch(tag)
    if match is None:
        raise ReleaseMetadataError(
            "Release tag must follow 'vMAJOR.MINOR.PATCH' (optional '-fork.N')."
        )
    return match.group("version")


def _normalize_release_date(raw_release_date: str | None) -> str:
    if raw_release_date is None:
        return date.today().isoformat()
    value = raw_release_date.strip()
    if not value:
        return date.today().isoformat()
    try:
        date.fromisoformat(value)
    except ValueError as exc:
        raise ReleaseMetadataError(
            "Release date must follow 'YYYY-MM-DD'."
        ) from exc
    return value


def _extract_canonical_version(content: str, pattern: str, file_path: Path) -> str:
    compiled = re.compile(pattern, re.MULTILINE)
    match = compiled.search(content)
    if match is None:
        raise ReleaseMetadataError(
            f"Could not extract canonical version from '{file_path}' using policy pattern."
        )
    if "version" in match.groupdict():
        return str(match.group("version")).strip()
    if match.groups():
        return str(match.group(1)).strip()
    raise ReleaseMetadataError(
        "Canonical pattern in policy must include capture group 'version' or first group."
    )


def _replace_canonical_version(content: str, pattern: str, new_version: str, file_path: Path) -> str:
    compiled = re.compile(pattern, re.MULTILINE)
    match = compiled.search(content)
    if match is None:
        raise ReleaseMetadataError(
            f"Could not locate canonical version line in '{file_path}' using policy pattern."
        )
    old_line = match.group(0)
    new_line = re.sub(r'"[^"]+"', f'"{new_version}"', old_line, count=1)
    if new_line == old_line:
        return content
    return content.replace(old_line, new_line, 1)


def _has_release_heading(changelog_content: str, heading_pattern: str, version: str) -> bool:
    regex = re.compile(heading_pattern, re.MULTILINE)
    for match in regex.finditer(changelog_content):
        if str(match.groupdict().get("version", "")).strip() == version:
            return True
        if not match.groupdict() and match.groups() and str(match.group(1)).strip() == version:
            return True
    return False


def _insert_release_heading(
    changelog_content: str,
    *,
    version: str,
    release_date: str,
    unreleased_heading: str,
) -> str:
    heading = f"## [{version}] - {release_date}"
    if heading in changelog_content:
        return changelog_content

    block = [
        heading,
        "",
        "### Added",
        "",
        "- *No changes documented yet.*",
        "",
    ]

    lines = changelog_content.splitlines()
    unreleased_index = -1
    for idx, line in enumerate(lines):
        if line.strip() == unreleased_heading:
            unreleased_index = idx
            break

    if unreleased_index == -1:
        base = changelog_content.rstrip("\n")
        suffix = "\n\n" + "\n".join(block)
        return base + suffix + "\n"

    # Insert immediately after [Unreleased] so existing unreleased entries
    # are moved under the new version heading.
    insert_at = unreleased_index + 1
    prefix = lines[:insert_at]
    suffix = lines[insert_at:]
    while suffix and not suffix[0].strip():
        suffix = suffix[1:]

    separator: list[str] = []
    if not prefix or prefix[-1].strip():
        separator = [""]
    new_lines = prefix + separator + block + suffix
    return "\n".join(new_lines).rstrip("\n") + "\n"


def _run_runtime_cli_version(repo_root: Path) -> str:
    cmd = ["uv", "run", "specify", "version"]
    try:
        result = subprocess.run(
            cmd,
            cwd=str(repo_root),
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError as exc:
        raise ReleaseMetadataError(f"Failed to execute runtime version check: {exc}") from exc

    if result.returncode != 0:
        stderr = (result.stderr or "").strip()
        raise ReleaseMetadataError(
            "Runtime version check failed while executing 'uv run specify version'"
            + (f": {stderr}" if stderr else ".")
        )

    match = re.search(
        r"CLI Version\s+([0-9]+\.[0-9]+\.[0-9]+(?:-fork\.[0-9]+)?)",
        result.stdout,
    )
    if match is None:
        raise ReleaseMetadataError(
            "Could not parse CLI Version from runtime output of 'uv run specify version'."
        )
    return match.group(1)


def check_release_metadata(
    *,
    repo_root: Path,
    policy: Policy,
    release_tag: str | None,
    enforce_release_match: bool,
    skip_runtime: bool,
) -> dict[str, Any]:
    canonical_path = repo_root / policy.canonical_file
    changelog_path = repo_root / policy.changelog_file

    if not canonical_path.exists():
        raise ReleaseMetadataError(f"Canonical version file not found: {canonical_path}")
    if not changelog_path.exists():
        raise ReleaseMetadataError(f"Changelog file not found: {changelog_path}")

    canonical_content = canonical_path.read_text(encoding="utf-8")
    changelog_content = changelog_path.read_text(encoding="utf-8")
    canonical_version = _extract_canonical_version(
        canonical_content, policy.canonical_pattern, canonical_path
    )

    errors: list[str] = []
    warnings: list[str] = []
    normalized_release_tag: str | None = None
    release_version: str | None = None

    if release_tag:
        normalized_release_tag = release_tag.strip()
        release_version = _normalize_release_tag(normalized_release_tag)
        if enforce_release_match and canonical_version != release_version:
            errors.append(
                f"Canonical version '{canonical_version}' does not match release tag '{normalized_release_tag}'."
            )

    if not _has_release_heading(changelog_content, policy.release_heading_pattern, canonical_version):
        errors.append(
            f"Missing changelog heading for version '{canonical_version}' in '{policy.changelog_file}'."
        )

    runtime_cli_version: str | None = None
    if not skip_runtime:
        try:
            runtime_cli_version = _run_runtime_cli_version(repo_root)
            if runtime_cli_version != canonical_version:
                errors.append(
                    f"Runtime CLI version '{runtime_cli_version}' does not match canonical version '{canonical_version}'."
                )
        except ReleaseMetadataError as exc:
            errors.append(str(exc))
    else:
        warnings.append("Runtime version check skipped by request.")

    return {
        "ok": len(errors) == 0,
        "canonical_version": canonical_version,
        "release_tag": normalized_release_tag,
        "release_version": release_version,
        "runtime_cli_version": runtime_cli_version,
        "errors": errors,
        "warnings": warnings,
        "policy_allowlist": list(policy.sync_allowlist),
    }


def sync_release_metadata(
    *,
    repo_root: Path,
    policy: Policy,
    release_tag: str,
    release_date: str,
) -> dict[str, Any]:
    canonical_path = repo_root / policy.canonical_file
    changelog_path = repo_root / policy.changelog_file
    release_version = _normalize_release_tag(release_tag)

    if not canonical_path.exists():
        raise ReleaseMetadataError(f"Canonical version file not found: {canonical_path}")
    if not changelog_path.exists():
        raise ReleaseMetadataError(f"Changelog file not found: {changelog_path}")

    current_canonical_content = canonical_path.read_text(encoding="utf-8")
    current_changelog_content = changelog_path.read_text(encoding="utf-8")
    current_version = _extract_canonical_version(
        current_canonical_content, policy.canonical_pattern, canonical_path
    )

    updated_canonical_content = _replace_canonical_version(
        current_canonical_content,
        policy.canonical_pattern,
        release_version,
        canonical_path,
    )
    updated_changelog_content = _insert_release_heading(
        current_changelog_content,
        version=release_version,
        release_date=release_date,
        unreleased_heading=policy.unreleased_heading,
    )

    changed_files: list[str] = []
    if updated_canonical_content != current_canonical_content:
        canonical_path.write_text(updated_canonical_content, encoding="utf-8")
        changed_files.append(policy.canonical_file)
    if updated_changelog_content != current_changelog_content:
        changelog_path.write_text(updated_changelog_content, encoding="utf-8")
        changed_files.append(policy.changelog_file)

    unexpected = sorted(set(changed_files) - set(policy.sync_allowlist))
    if unexpected:
        raise ReleaseMetadataError(
            "Sync produced unexpected file changes outside allowlist: "
            + ", ".join(unexpected)
        )

    return {
        "ok": True,
        "release_tag": release_tag,
        "release_version": release_version,
        "previous_version": current_version,
        "changed_files": sorted(changed_files),
        "changed": bool(changed_files),
    }


def _cmd_check(args: argparse.Namespace) -> int:
    root = _as_repo_root(args.repo_root)
    policy = _load_policy(root, args.policy)
    payload = check_release_metadata(
        repo_root=root,
        policy=policy,
        release_tag=args.release_tag,
        enforce_release_match=args.enforce_release_match,
        skip_runtime=args.skip_runtime,
    )
    if args.json:
        print(json.dumps(payload))
    else:
        print(json.dumps(payload, indent=2))
    return 0 if payload["ok"] else 1


def _cmd_sync(args: argparse.Namespace) -> int:
    root = _as_repo_root(args.repo_root)
    policy = _load_policy(root, args.policy)
    release_date = _normalize_release_date(args.release_date)
    payload = sync_release_metadata(
        repo_root=root,
        policy=policy,
        release_tag=args.release_tag,
        release_date=release_date,
    )
    if args.json:
        print(json.dumps(payload))
    else:
        print(json.dumps(payload, indent=2))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Release metadata consistency guard/sync utility."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    check_parser = subparsers.add_parser(
        "check",
        help="Validate release metadata consistency against policy.",
    )
    check_parser.add_argument(
        "--repo-root",
        default=".",
        help="Repository root (default: current directory).",
    )
    check_parser.add_argument(
        "--policy",
        default=".github/release-version-policy.yml",
        help="Path to release metadata policy file.",
    )
    check_parser.add_argument(
        "--release-tag",
        default=None,
        help="Optional release tag (vMAJOR.MINOR.PATCH) for release-to-repo checks.",
    )
    check_parser.add_argument(
        "--enforce-release-match",
        action="store_true",
        help="Fail when canonical version differs from provided release tag.",
    )
    check_parser.add_argument(
        "--skip-runtime",
        action="store_true",
        help="Skip `uv run specify version` runtime coherence check.",
    )
    check_parser.add_argument(
        "--json",
        action="store_true",
        help="Emit compact JSON output.",
    )
    check_parser.set_defaults(handler=_cmd_check)

    sync_parser = subparsers.add_parser(
        "sync",
        help="Synchronize release metadata files to a published tag.",
    )
    sync_parser.add_argument(
        "--repo-root",
        default=".",
        help="Repository root (default: current directory).",
    )
    sync_parser.add_argument(
        "--policy",
        default=".github/release-version-policy.yml",
        help="Path to release metadata policy file.",
    )
    sync_parser.add_argument(
        "--release-tag",
        required=True,
        help="Target release tag (vMAJOR.MINOR.PATCH).",
    )
    sync_parser.add_argument(
        "--release-date",
        default=None,
        help="Release date (YYYY-MM-DD). Defaults to current UTC date.",
    )
    sync_parser.add_argument(
        "--json",
        action="store_true",
        help="Emit compact JSON output.",
    )
    sync_parser.set_defaults(handler=_cmd_sync)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return int(args.handler(args))
    except ReleaseMetadataError as exc:
        print(str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
