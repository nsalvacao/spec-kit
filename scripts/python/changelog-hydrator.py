#!/usr/bin/env python3
"""Hydrate a release heading in CHANGELOG.md from GitHub release notes body."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


def _extract_release_bullets(body: str) -> list[str]:
    lines = body.splitlines()
    start_idx = None
    for idx, line in enumerate(lines):
        if line.strip().lower() == "## changelog":
            start_idx = idx + 1
            break

    candidates: list[str] = []
    scan_lines = lines[start_idx:] if start_idx is not None else lines

    for line in scan_lines:
        stripped = line.strip()
        if start_idx is not None and stripped.startswith("## "):
            break
        if stripped.startswith("- "):
            candidates.append(stripped)

    # Preserve order while dropping duplicates/empties.
    seen: set[str] = set()
    bullets: list[str] = []
    for line in candidates:
        if line and line not in seen:
            seen.add(line)
            bullets.append(line)
    return bullets


def _hydrate_changelog(
    changelog_content: str,
    *,
    version: str,
    placeholder: str,
    bullets: list[str],
) -> tuple[str, bool, str]:
    if not bullets:
        return changelog_content, False, "no_release_bullets_found"

    release_heading = re.compile(
        rf"^## \[{re.escape(version)}\] - [0-9]{{4}}-[0-9]{{2}}-[0-9]{{2}}$",
        flags=re.MULTILINE,
    )
    match = release_heading.search(changelog_content)
    if match is None:
        return changelog_content, False, "release_heading_not_found"

    lines = changelog_content.splitlines()
    start_line = changelog_content[: match.start()].count("\n")
    end_line = len(lines)
    for idx in range(start_line + 1, len(lines)):
        if lines[idx].startswith("## ["):
            end_line = idx
            break

    section = lines[start_line:end_line]
    new_section: list[str] = []
    replaced = False
    for line in section:
        if line.strip() == placeholder:
            if not replaced:
                new_section.extend(bullets)
                replaced = True
            continue
        new_section.append(line)

    if not replaced:
        return changelog_content, False, "placeholder_not_present"

    new_lines = lines[:start_line] + new_section + lines[end_line:]
    new_content = "\n".join(new_lines).rstrip("\n") + "\n"
    return new_content, True, "hydrated"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--changelog", required=True, help="Path to CHANGELOG.md")
    parser.add_argument("--version", required=True, help="Release version without v prefix")
    parser.add_argument("--release-body-file", required=True, help="Path to release body text file")
    parser.add_argument(
        "--placeholder",
        default="- *No changes documented yet.*",
        help="Placeholder line to replace inside target release section",
    )
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args()

    changelog_path = Path(args.changelog)
    body_path = Path(args.release_body_file)

    if not changelog_path.is_file():
        print(f"Error: changelog file not found: {changelog_path}", file=sys.stderr)
        return 1
    if not body_path.is_file():
        print(f"Error: release body file not found: {body_path}", file=sys.stderr)
        return 1

    changelog = changelog_path.read_text(encoding="utf-8")
    body = body_path.read_text(encoding="utf-8")
    bullets = _extract_release_bullets(body)
    updated, changed, reason = _hydrate_changelog(
        changelog,
        version=args.version.strip(),
        placeholder=args.placeholder,
        bullets=bullets,
    )

    if changed:
        changelog_path.write_text(updated, encoding="utf-8")

    payload = {
        "ok": True,
        "changed": changed,
        "reason": reason,
        "version": args.version.strip(),
        "bullet_count": len(bullets),
        "changelog": str(changelog_path),
    }

    if args.as_json:
        print(json.dumps(payload))
    else:
        print(
            f"changed={str(changed).lower()} reason={reason} "
            f"version={args.version.strip()} bullets={len(bullets)}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
