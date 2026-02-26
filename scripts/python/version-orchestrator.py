#!/usr/bin/env python3
"""Manifest-driven version bump and coherence checks (issue #165)."""

from __future__ import annotations

import argparse
import difflib
import json
import re
import subprocess
import sys
from dataclasses import dataclass
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

import yaml


SEMVER_PATTERN = re.compile(
    r"^(?P<major>[0-9]+)\.(?P<minor>[0-9]+)\.(?P<patch>[0-9]+)(?:-fork\.(?P<fork>[0-9]+))?$"
)
ALLOWED_RUNTIME_COMMAND = ("uv", "run", "specify", "version")
MAX_DIFF_PREVIEW_CHARS = 200_000


class VersionOrchestrationError(ValueError):
    """Raised when version orchestration validation fails."""


@dataclass(frozen=True)
class MatchRule:
    file: str
    pattern: str
    expected_matches: int = 1


@dataclass(frozen=True)
class ChangelogRule:
    file: str
    unreleased_heading: str
    release_heading_pattern: str
    scaffold_heading: str
    scaffold_placeholder: str


@dataclass(frozen=True)
class RuntimeRule:
    command: tuple[str, ...]
    version_pattern: str


@dataclass(frozen=True)
class VersionMap:
    canonical: MatchRule
    targets: tuple[MatchRule, ...]
    changelog: ChangelogRule
    runtime: RuntimeRule
    tag_pattern: str
    allowlist: tuple[str, ...]


def _as_repo_root(repo_root: str | Path) -> Path:
    raw = str(repo_root).strip() if repo_root is not None else ""
    if not raw:
        raise VersionOrchestrationError("Repository root must be a non-empty path.")
    root = Path(raw).expanduser().resolve()
    if not root.exists() or not root.is_dir():
        raise VersionOrchestrationError(f"Repository root does not exist: {root}")
    return root


def _resolve_repo_file(repo_root: Path, relative_path: str) -> Path:
    root = repo_root.resolve()
    raw = str(relative_path).strip()
    if not raw:
        raise VersionOrchestrationError("Manifest file path must be non-empty.")
    candidate = (root / raw).resolve()
    try:
        candidate.relative_to(root)
    except ValueError as exc:
        raise VersionOrchestrationError(
            f"Path '{relative_path}' resolves outside repository root."
        ) from exc
    return candidate


def _compile_pattern(pattern: str, *, context: str) -> re.Pattern[str]:
    try:
        compiled = re.compile(pattern, re.MULTILINE)
    except re.error as exc:
        raise VersionOrchestrationError(
            f"Invalid regex for {context}: {exc}"
        ) from exc
    if "version" not in compiled.groupindex:
        raise VersionOrchestrationError(
            f"Regex for {context} must define a named capture group 'version'."
        )
    return compiled


def _load_version_map(repo_root: Path, map_path: str | Path) -> VersionMap:
    raw_map = str(map_path).strip() if map_path is not None else ""
    if not raw_map:
        raise VersionOrchestrationError("Version map path must be a non-empty path.")
    path = Path(raw_map)
    if not path.is_absolute():
        path = repo_root / path
    path = path.resolve()
    if not path.exists() or not path.is_file():
        raise VersionOrchestrationError(f"Version map file not found: {path}")

    try:
        raw_content = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise VersionOrchestrationError(
            f"Failed to read version map file '{path}': {exc}"
        ) from exc

    try:
        payload = yaml.safe_load(raw_content) or {}
    except yaml.YAMLError as exc:
        raise VersionOrchestrationError(f"Invalid YAML in version map '{path}': {exc}") from exc

    if not isinstance(payload, dict):
        raise VersionOrchestrationError("Version map root must be a mapping.")

    canonical_cfg = payload.get("canonical") or {}
    targets_cfg = payload.get("targets") or []
    changelog_cfg = payload.get("changelog") or {}
    runtime_cfg = payload.get("runtime") or {}
    tagging_cfg = payload.get("tagging") or {}
    sync_cfg = payload.get("sync") or {}
    allowlist = sync_cfg.get("allowlist") or []

    if not isinstance(canonical_cfg, dict):
        raise VersionOrchestrationError("'canonical' must be a mapping.")
    if not isinstance(targets_cfg, list):
        raise VersionOrchestrationError("'targets' must be a list.")
    if not isinstance(changelog_cfg, dict):
        raise VersionOrchestrationError("'changelog' must be a mapping.")
    if not isinstance(runtime_cfg, dict):
        raise VersionOrchestrationError("'runtime' must be a mapping.")
    if not isinstance(tagging_cfg, dict):
        raise VersionOrchestrationError("'tagging' must be a mapping.")
    if not isinstance(allowlist, list) or any(not isinstance(item, str) for item in allowlist):
        raise VersionOrchestrationError("'sync.allowlist' must be a list of strings.")

    canonical_file = str(canonical_cfg.get("file", "")).strip()
    canonical_pattern = str(canonical_cfg.get("pattern", "")).strip()
    if not canonical_file or not canonical_pattern:
        raise VersionOrchestrationError("Canonical rule requires 'file' and 'pattern'.")

    targets: list[MatchRule] = []
    for idx, target in enumerate(targets_cfg, start=1):
        if not isinstance(target, dict):
            raise VersionOrchestrationError(f"Target #{idx} must be a mapping.")
        target_file = str(target.get("file", "")).strip()
        target_pattern = str(target.get("pattern", "")).strip()
        expected_matches_raw = target.get("expected_matches", 1)
        if not target_file or not target_pattern:
            raise VersionOrchestrationError(
                f"Target #{idx} requires 'file' and 'pattern'."
            )
        if not isinstance(expected_matches_raw, int) or expected_matches_raw < 1:
            raise VersionOrchestrationError(
                f"Target #{idx} has invalid expected_matches '{expected_matches_raw}'."
            )
        targets.append(
            MatchRule(
                file=target_file,
                pattern=target_pattern,
                expected_matches=expected_matches_raw,
            )
        )

    changelog_file = str(changelog_cfg.get("file", "")).strip()
    unreleased_heading = str(changelog_cfg.get("unreleased_heading", "")).strip()
    release_heading_pattern = str(changelog_cfg.get("release_heading_pattern", "")).strip()
    scaffold_heading = str(changelog_cfg.get("scaffold_heading", "")).strip() or "### Added"
    scaffold_placeholder = str(changelog_cfg.get("scaffold_placeholder", "")).strip()
    if not changelog_file or not unreleased_heading or not release_heading_pattern:
        raise VersionOrchestrationError(
            "Changelog rule requires 'file', 'unreleased_heading', and 'release_heading_pattern'."
        )
    if not scaffold_placeholder:
        raise VersionOrchestrationError(
            "Changelog rule requires non-empty 'scaffold_placeholder'."
        )

    runtime_command = runtime_cfg.get("command")
    runtime_pattern = str(runtime_cfg.get("version_pattern", "")).strip()
    if (
        not isinstance(runtime_command, list)
        or not runtime_command
        or any(not isinstance(item, str) or not item.strip() for item in runtime_command)
    ):
        raise VersionOrchestrationError("Runtime rule requires non-empty list 'command'.")
    if not runtime_pattern:
        raise VersionOrchestrationError("Runtime rule requires 'version_pattern'.")
    normalized_runtime_command = tuple(str(item).strip() for item in runtime_command)
    runtime_executable = normalized_runtime_command[0]
    if "/" in runtime_executable or "\\" in runtime_executable:
        raise VersionOrchestrationError(
            "Runtime command executable must be a tool name, not a path."
        )
    if any("\n" in item or "\r" in item for item in normalized_runtime_command):
        raise VersionOrchestrationError(
            "Runtime command arguments must not contain newline characters."
        )
    if normalized_runtime_command != ALLOWED_RUNTIME_COMMAND:
        raise VersionOrchestrationError(
            "Runtime command must match allowlisted prefix: "
            + " ".join(ALLOWED_RUNTIME_COMMAND)
        )

    tag_pattern = str(tagging_cfg.get("tag_pattern", "")).strip()
    if not tag_pattern:
        raise VersionOrchestrationError("Tagging rule requires 'tag_pattern'.")

    # Validate regex upfront for fast failures.
    _compile_pattern(canonical_pattern, context="canonical.pattern")
    for idx, target in enumerate(targets, start=1):
        _compile_pattern(target.pattern, context=f"targets[{idx}].pattern")
    _compile_pattern(release_heading_pattern, context="changelog.release_heading_pattern")
    _compile_pattern(runtime_pattern, context="runtime.version_pattern")
    _compile_pattern(tag_pattern, context="tagging.tag_pattern")

    return VersionMap(
        canonical=MatchRule(
            file=canonical_file,
            pattern=canonical_pattern,
            expected_matches=1,
        ),
        targets=tuple(targets),
        changelog=ChangelogRule(
            file=changelog_file,
            unreleased_heading=unreleased_heading,
            release_heading_pattern=release_heading_pattern,
            scaffold_heading=scaffold_heading,
            scaffold_placeholder=scaffold_placeholder,
        ),
        runtime=RuntimeRule(
            command=normalized_runtime_command,
            version_pattern=runtime_pattern,
        ),
        tag_pattern=tag_pattern,
        allowlist=tuple(sorted(set(item.strip() for item in allowlist if item.strip()))),
    )


def _extract_version_matches(
    *,
    content: str,
    file_path: Path,
    rule: MatchRule,
    context: str,
) -> tuple[str, list[re.Match[str]], re.Pattern[str]]:
    regex = _compile_pattern(rule.pattern, context=context)
    matches = list(regex.finditer(content))
    if len(matches) != rule.expected_matches:
        raise VersionOrchestrationError(
            f"{context} expected {rule.expected_matches} match(es) in '{file_path}', found {len(matches)}."
        )
    versions = [str(match.group("version")).strip() for match in matches]
    unique_versions = sorted(set(versions))
    if len(unique_versions) != 1:
        raise VersionOrchestrationError(
            f"{context} in '{file_path}' has inconsistent captured versions: {', '.join(unique_versions)}."
        )
    return unique_versions[0], matches, regex


def _replace_version_captures(
    *,
    content: str,
    matches: list[re.Match[str]],
    new_version: str,
) -> str:
    updated = content
    for match in reversed(matches):
        start, end = match.span("version")
        updated = updated[:start] + new_version + updated[end:]
    return updated


def _read_required_file(repo_root: Path, relative_path: str) -> tuple[Path, str]:
    file_path = _resolve_repo_file(repo_root, relative_path)
    if not file_path.exists() or not file_path.is_file():
        raise VersionOrchestrationError(f"Required file not found: {file_path}")
    try:
        return file_path, file_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise VersionOrchestrationError(f"Failed to read required file '{file_path}': {exc}") from exc


def _has_release_heading(changelog_content: str, heading_pattern: str, version: str) -> bool:
    regex = _compile_pattern(heading_pattern, context="changelog.release_heading_pattern")
    for match in regex.finditer(changelog_content):
        if str(match.group("version")).strip() == version:
            return True
    return False


def _insert_release_heading(
    changelog_content: str,
    *,
    version: str,
    release_date: str,
    rule: ChangelogRule,
) -> str:
    heading = f"## [{version}] - {release_date}"
    if heading in changelog_content:
        return changelog_content

    block = [
        heading,
        "",
        rule.scaffold_heading,
        "",
        rule.scaffold_placeholder,
        "",
    ]

    lines = changelog_content.splitlines()
    unreleased_index = -1
    for idx, line in enumerate(lines):
        if line.strip() == rule.unreleased_heading:
            unreleased_index = idx
            break

    if unreleased_index == -1:
        base = changelog_content.rstrip("\n")
        suffix = "\n\n" + "\n".join(block)
        return base + suffix + "\n"

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


def _normalize_release_date(raw_release_date: str | None) -> str:
    if raw_release_date is None:
        return datetime.now(timezone.utc).date().isoformat()
    value = str(raw_release_date).strip()
    if not value:
        return datetime.now(timezone.utc).date().isoformat()
    try:
        date.fromisoformat(value)
    except ValueError as exc:
        raise VersionOrchestrationError(
            "Release date must be a valid UTC date in 'YYYY-MM-DD' format."
        ) from exc
    return value


def _normalize_release_tag(release_tag: str, tag_pattern: str) -> str:
    tag = (release_tag or "").strip()
    if not tag:
        raise VersionOrchestrationError("Release tag must be a non-empty string.")
    regex = _compile_pattern(tag_pattern, context="tagging.tag_pattern")
    match = regex.fullmatch(tag)
    if match is None:
        raise VersionOrchestrationError("Release tag does not match tagging.tag_pattern.")
    return str(match.group("version")).strip()


def _run_runtime_cli_version(repo_root: Path, runtime_rule: RuntimeRule) -> str:
    try:
        result = subprocess.run(
            list(runtime_rule.command),
            cwd=str(repo_root),
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError as exc:
        raise VersionOrchestrationError(f"Failed to execute runtime check: {exc}") from exc

    if result.returncode != 0:
        stderr = (result.stderr or "").strip()
        raise VersionOrchestrationError(
            "Runtime version check failed while executing "
            + "'{}'".format(" ".join(runtime_rule.command))
            + (f": {stderr}" if stderr else ".")
        )

    regex = _compile_pattern(runtime_rule.version_pattern, context="runtime.version_pattern")
    match = regex.search(result.stdout)
    if match is None:
        raise VersionOrchestrationError(
            "Could not parse runtime CLI version from command output."
        )
    return str(match.group("version")).strip()


def _bump_semver(version: str, part: str) -> str:
    match = SEMVER_PATTERN.fullmatch(version.strip())
    if match is None:
        raise VersionOrchestrationError(
            f"Canonical version '{version}' is not a supported semantic version."
        )
    if match.group("fork") is not None:
        raise VersionOrchestrationError(
            "Automatic bump does not support '-fork.N' version suffixes."
        )
    major = int(match.group("major"))
    minor = int(match.group("minor"))
    patch = int(match.group("patch"))

    if part == "patch":
        patch += 1
    elif part == "minor":
        minor += 1
        patch = 0
    elif part == "major":
        major += 1
        minor = 0
        patch = 0
    else:
        raise VersionOrchestrationError(f"Unsupported bump part: {part}")
    return f"{major}.{minor}.{patch}"


def _build_diff_preview(
    *,
    old_contents: dict[str, str],
    new_contents: dict[str, str],
) -> str:
    chunks: list[str] = []
    for rel_path in sorted(new_contents):
        old = old_contents.get(rel_path, "")
        new = new_contents[rel_path]
        if old == new:
            continue
        diff = difflib.unified_diff(
            old.splitlines(keepends=True),
            new.splitlines(keepends=True),
            fromfile=f"a/{rel_path}",
            tofile=f"b/{rel_path}",
        )
        chunks.append("".join(diff))
    combined = "\n".join(chunk for chunk in chunks if chunk)
    if len(combined) <= MAX_DIFF_PREVIEW_CHARS:
        return combined
    truncated = combined[:MAX_DIFF_PREVIEW_CHARS]
    return (
        truncated
        + "\n\n... [diff truncated: exceeded "
        + f"{MAX_DIFF_PREVIEW_CHARS} characters]"
    )


def check_version_coherence(
    *,
    repo_root: Path,
    version_map: VersionMap,
    release_tag: str | None,
    enforce_release_match: bool,
    skip_runtime: bool,
) -> dict[str, Any]:
    canonical_path, canonical_content = _read_required_file(repo_root, version_map.canonical.file)
    canonical_version, _, _ = _extract_version_matches(
        content=canonical_content,
        file_path=canonical_path,
        rule=version_map.canonical,
        context="canonical",
    )

    errors: list[str] = []
    warnings: list[str] = []
    target_versions: list[dict[str, str]] = []

    for target in version_map.targets:
        target_path, target_content = _read_required_file(repo_root, target.file)
        target_version, _, _ = _extract_version_matches(
            content=target_content,
            file_path=target_path,
            rule=target,
            context=f"target:{target.file}",
        )
        target_versions.append({"file": target.file, "version": target_version})
        if target_version != canonical_version:
            errors.append(
                f"Target '{target.file}' version '{target_version}' does not match canonical version '{canonical_version}'."
            )

    changelog_path, changelog_content = _read_required_file(repo_root, version_map.changelog.file)
    if not _has_release_heading(
        changelog_content,
        version_map.changelog.release_heading_pattern,
        canonical_version,
    ):
        errors.append(
            f"Missing changelog heading for canonical version '{canonical_version}' in '{version_map.changelog.file}'."
        )

    release_version: str | None = None
    if release_tag:
        release_version = _normalize_release_tag(release_tag, version_map.tag_pattern)
        if enforce_release_match and release_version != canonical_version:
            errors.append(
                f"Canonical version '{canonical_version}' does not match release tag '{release_tag}'."
            )

    runtime_cli_version: str | None = None
    if skip_runtime:
        warnings.append("Runtime version check skipped by request.")
    else:
        try:
            runtime_cli_version = _run_runtime_cli_version(repo_root, version_map.runtime)
            if runtime_cli_version != canonical_version:
                errors.append(
                    f"Runtime CLI version '{runtime_cli_version}' does not match canonical version '{canonical_version}'."
                )
        except VersionOrchestrationError as exc:
            errors.append(str(exc))

    return {
        "ok": len(errors) == 0,
        "canonical_version": canonical_version,
        "target_versions": target_versions,
        "release_tag": release_tag,
        "release_version": release_version,
        "runtime_cli_version": runtime_cli_version,
        "errors": errors,
        "warnings": warnings,
        "allowlist": list(version_map.allowlist),
        "canonical_file": str(version_map.canonical.file),
        "changelog_file": str(changelog_path.relative_to(repo_root)),
    }


def _validate_target_version(version: str) -> str:
    normalized = str(version).strip()
    if not normalized:
        raise VersionOrchestrationError("Target version must be a non-empty string.")
    if SEMVER_PATTERN.fullmatch(normalized) is None:
        raise VersionOrchestrationError(
            f"Target version '{normalized}' is not a supported semantic version."
        )
    return normalized


def _apply_target_version(
    *,
    repo_root: Path,
    version_map: VersionMap,
    target_version: str,
    release_date: str,
    dry_run: bool,
    include_diff: bool,
    source: str,
) -> dict[str, Any]:
    old_contents: dict[str, str] = {}
    new_contents: dict[str, str] = {}

    canonical_path, canonical_content = _read_required_file(repo_root, version_map.canonical.file)
    old_contents[version_map.canonical.file] = canonical_content

    canonical_version, canonical_matches, _ = _extract_version_matches(
        content=canonical_content,
        file_path=canonical_path,
        rule=version_map.canonical,
        context="canonical",
    )
    next_version = _validate_target_version(target_version)
    updated_canonical = _replace_version_captures(
        content=canonical_content,
        matches=canonical_matches,
        new_version=next_version,
    )
    new_contents[version_map.canonical.file] = updated_canonical

    for target in version_map.targets:
        target_path, target_content = _read_required_file(repo_root, target.file)
        old_contents[target.file] = target_content
        _, target_matches, _ = _extract_version_matches(
            content=target_content,
            file_path=target_path,
            rule=target,
            context=f"target:{target.file}",
        )
        updated_target = _replace_version_captures(
            content=target_content,
            matches=target_matches,
            new_version=next_version,
        )
        new_contents[target.file] = updated_target

    changelog_path, changelog_content = _read_required_file(repo_root, version_map.changelog.file)
    old_contents[version_map.changelog.file] = changelog_content
    updated_changelog = _insert_release_heading(
        changelog_content,
        version=next_version,
        release_date=release_date,
        rule=version_map.changelog,
    )
    new_contents[version_map.changelog.file] = updated_changelog

    changed_files = sorted(
        [path for path, updated in new_contents.items() if old_contents.get(path, "") != updated]
    )

    unexpected = sorted(set(changed_files) - set(version_map.allowlist))
    if unexpected:
        raise VersionOrchestrationError(
            "Version update produced unexpected changes outside allowlist: "
            + ", ".join(unexpected)
        )

    diff_preview = ""
    if include_diff or dry_run:
        diff_preview = _build_diff_preview(old_contents=old_contents, new_contents=new_contents)

    if not dry_run:
        for rel_path in changed_files:
            resolved = _resolve_repo_file(repo_root, rel_path)
            try:
                resolved.write_text(new_contents[rel_path], encoding="utf-8")
            except OSError as exc:
                raise VersionOrchestrationError(
                    f"Failed to write updated file '{rel_path}': {exc}"
                ) from exc

    return {
        "ok": True,
        "changed": bool(changed_files),
        "dry_run": dry_run,
        "source": source,
        "previous_version": canonical_version,
        "next_version": next_version,
        "release_date": release_date,
        "changed_files": changed_files,
        "allowlist": list(version_map.allowlist),
        "diff_preview": diff_preview,
    }


def bump_version(
    *,
    repo_root: Path,
    version_map: VersionMap,
    part: str,
    release_date: str,
    dry_run: bool,
    include_diff: bool,
) -> dict[str, Any]:
    canonical_path, canonical_content = _read_required_file(repo_root, version_map.canonical.file)
    canonical_version, _, _ = _extract_version_matches(
        content=canonical_content,
        file_path=canonical_path,
        rule=version_map.canonical,
        context="canonical",
    )
    next_version = _bump_semver(canonical_version, part)
    payload = _apply_target_version(
        repo_root=repo_root,
        version_map=version_map,
        target_version=next_version,
        release_date=release_date,
        dry_run=dry_run,
        include_diff=include_diff,
        source=f"bump:{part}",
    )
    payload["part"] = part
    return payload


def sync_version(
    *,
    repo_root: Path,
    version_map: VersionMap,
    target_version: str,
    release_date: str,
    dry_run: bool,
    include_diff: bool,
    source: str,
) -> dict[str, Any]:
    return _apply_target_version(
        repo_root=repo_root,
        version_map=version_map,
        target_version=target_version,
        release_date=release_date,
        dry_run=dry_run,
        include_diff=include_diff,
        source=source,
    )


def _cmd_check(args: argparse.Namespace) -> int:
    root = _as_repo_root(args.repo_root)
    version_map = _load_version_map(root, args.map)
    payload = check_version_coherence(
        repo_root=root,
        version_map=version_map,
        release_tag=args.release_tag,
        enforce_release_match=args.enforce_release_match,
        skip_runtime=args.skip_runtime,
    )
    if args.json:
        print(json.dumps(payload))
    else:
        print(json.dumps(payload, indent=2))
    return 0 if payload["ok"] else 1


def _cmd_bump(args: argparse.Namespace) -> int:
    root = _as_repo_root(args.repo_root)
    version_map = _load_version_map(root, args.map)
    payload = bump_version(
        repo_root=root,
        version_map=version_map,
        part=args.part,
        release_date=_normalize_release_date(args.release_date),
        dry_run=args.dry_run,
        include_diff=args.include_diff,
    )
    if args.json:
        print(json.dumps(payload))
    else:
        print(json.dumps(payload, indent=2))
    return 0


def _cmd_sync(args: argparse.Namespace) -> int:
    root = _as_repo_root(args.repo_root)
    version_map = _load_version_map(root, args.map)

    if bool(args.target_version) == bool(args.release_tag):
        raise VersionOrchestrationError(
            "Provide one and only one of --target-version or --release-tag."
        )

    source = "sync:target-version"
    target_version = ""
    if args.target_version:
        target_version = _validate_target_version(args.target_version)
    else:
        target_version = _normalize_release_tag(args.release_tag, version_map.tag_pattern)
        source = "sync:release-tag"

    payload = sync_version(
        repo_root=root,
        version_map=version_map,
        target_version=target_version,
        release_date=_normalize_release_date(args.release_date),
        dry_run=args.dry_run,
        include_diff=args.include_diff,
        source=source,
    )
    if args.release_tag:
        payload["release_tag"] = args.release_tag

    if args.json:
        print(json.dumps(payload))
    else:
        print(json.dumps(payload, indent=2))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Manifest-driven version bump and coherence checks."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    check_parser = subparsers.add_parser(
        "check",
        help="Validate canonical/targets/changelog/runtime coherence.",
    )
    check_parser.add_argument(
        "--repo-root",
        default=".",
        help="Repository root (default: current directory).",
    )
    check_parser.add_argument(
        "--map",
        default=".github/version-map.yml",
        help="Path to version map manifest.",
    )
    check_parser.add_argument(
        "--release-tag",
        default=None,
        help="Optional release tag to validate against canonical version.",
    )
    check_parser.add_argument(
        "--enforce-release-match",
        action="store_true",
        help="Fail when canonical version differs from --release-tag.",
    )
    check_parser.add_argument(
        "--skip-runtime",
        action="store_true",
        help="Skip runtime check command configured in the manifest.",
    )
    check_parser.add_argument(
        "--json",
        action="store_true",
        help="Emit compact JSON output.",
    )
    check_parser.set_defaults(handler=_cmd_check)

    bump_parser = subparsers.add_parser(
        "bump",
        help="Bump semantic version and propagate via manifest map.",
    )
    bump_parser.add_argument(
        "--repo-root",
        default=".",
        help="Repository root (default: current directory).",
    )
    bump_parser.add_argument(
        "--map",
        default=".github/version-map.yml",
        help="Path to version map manifest.",
    )
    bump_parser.add_argument(
        "--part",
        required=True,
        choices=["patch", "minor", "major"],
        help="Semantic version segment to bump.",
    )
    bump_parser.add_argument(
        "--release-date",
        default=None,
        help="Release date (YYYY-MM-DD) for changelog heading. Defaults to current UTC date.",
    )
    bump_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Compute and report changes without writing files.",
    )
    bump_parser.add_argument(
        "--include-diff",
        action="store_true",
        help="Include unified diff preview in output.",
    )
    bump_parser.add_argument(
        "--json",
        action="store_true",
        help="Emit compact JSON output.",
    )
    bump_parser.set_defaults(handler=_cmd_bump)

    sync_parser = subparsers.add_parser(
        "sync",
        help="Synchronize canonical/targets to a specific target version or release tag.",
    )
    sync_parser.add_argument(
        "--repo-root",
        default=".",
        help="Repository root (default: current directory).",
    )
    sync_parser.add_argument(
        "--map",
        default=".github/version-map.yml",
        help="Path to version map manifest.",
    )
    sync_parser.add_argument(
        "--target-version",
        default=None,
        help="Target semantic version (example: 0.0.54).",
    )
    sync_parser.add_argument(
        "--release-tag",
        default=None,
        help="Target release tag context (example: v0.0.54).",
    )
    sync_parser.add_argument(
        "--release-date",
        default=None,
        help="Release date (YYYY-MM-DD) for changelog heading. Defaults to current UTC date.",
    )
    sync_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Compute and report changes without writing files.",
    )
    sync_parser.add_argument(
        "--include-diff",
        action="store_true",
        help="Include unified diff preview in output.",
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
    except VersionOrchestrationError as exc:
        print(str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
