#!/usr/bin/env python3
"""Compliance checker for legal/trademark/provenance gates (issue #178).

Checks:
  - LICENSE file is present at the repository root.
  - Required compliance markers are present in key documentation files.
  - Non-affiliation statement appears in README.md.
  - MIT license reference appears in README.md.
  - Trademark notice appears in docs/trademarks.md.
  - When upstream-intake entries appear in CHANGELOG.md, provenance lines
    (``Source PR:``) are present in those entries.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

COMPLIANCE_MARKER = "legal-compliance:v1"

# Phrase required in docs/legal-compliance.md
LEGAL_COMPLIANCE_MARKERS: tuple[str, ...] = (COMPLIANCE_MARKER,)

# Phrases required in README.md (case-insensitive substring match)
README_REQUIRED_PHRASES: tuple[str, ...] = (
    "not affiliated with github",
    "mit",
)

# Phrase required in docs/trademarks.md (case-insensitive)
TRADEMARKS_REQUIRED_PHRASE = "attribution only"

# Trigger keywords in CHANGELOG.md that require a provenance line
UPSTREAM_INTAKE_KEYWORDS: tuple[str, ...] = (
    "upstream pr",
    "upstream intake",
)

# Provenance line pattern that must follow an upstream-intake entry
PROVENANCE_LINE_PATTERN = re.compile(r"source pr\s*:", re.IGNORECASE)
PROVENANCE_LOOKAHEAD_LINES = 10  # lines after a trigger keyword to search for a provenance line
# Paths relative to repo root that are always checked
LICENSE_PATH = "LICENSE"
README_PATH = "README.md"
LEGAL_DOC_PATH = "docs/legal-compliance.md"
TRADEMARKS_PATH = "docs/trademarks.md"
CHANGELOG_PATH = "CHANGELOG.md"


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------


@dataclass
class ComplianceViolation:
    check: str
    path: str
    message: str

    def to_dict(self) -> dict[str, str]:
        return {"check": self.check, "path": self.path, "message": self.message}


@dataclass
class ComplianceResult:
    ok: bool
    checks_run: list[str] = field(default_factory=list)
    violations: list[ComplianceViolation] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "ok": self.ok,
            "checks_run": self.checks_run,
            "violations": [v.to_dict() for v in self.violations],
        }


# ---------------------------------------------------------------------------
# Individual checks
# ---------------------------------------------------------------------------


def _check_license_present(repo_root: Path) -> list[ComplianceViolation]:
    """Verify LICENSE file exists at the repository root."""
    license_file = repo_root / LICENSE_PATH
    if not license_file.is_file():
        return [
            ComplianceViolation(
                check="license_present",
                path=LICENSE_PATH,
                message="LICENSE file is missing from the repository root. "
                "MIT redistribution requires including a verbatim copy.",
            )
        ]
    return []


def _check_legal_compliance_markers(repo_root: Path) -> list[ComplianceViolation]:
    """Verify docs/legal-compliance.md exists and contains required markers."""
    doc = repo_root / LEGAL_DOC_PATH
    if not doc.is_file():
        return [
            ComplianceViolation(
                check="legal_compliance_doc",
                path=LEGAL_DOC_PATH,
                message="docs/legal-compliance.md is missing. "
                "Create it with the required compliance marker.",
            )
        ]

    content = doc.read_text(encoding="utf-8")
    violations: list[ComplianceViolation] = []
    for marker in LEGAL_COMPLIANCE_MARKERS:
        if marker not in content:
            violations.append(
                ComplianceViolation(
                    check="legal_compliance_marker",
                    path=LEGAL_DOC_PATH,
                    message=f"Required compliance marker not found: '{marker}'. "
                    "Add the marker to docs/legal-compliance.md.",
                )
            )
    return violations


def _check_readme_phrases(repo_root: Path) -> list[ComplianceViolation]:
    """Verify README.md contains required non-affiliation and MIT phrases."""
    readme = repo_root / README_PATH
    if not readme.is_file():
        return [
            ComplianceViolation(
                check="readme_present",
                path=README_PATH,
                message="README.md is missing.",
            )
        ]

    content = readme.read_text(encoding="utf-8").lower()
    violations: list[ComplianceViolation] = []
    for phrase in README_REQUIRED_PHRASES:
        if phrase not in content:
            violations.append(
                ComplianceViolation(
                    check="readme_required_phrase",
                    path=README_PATH,
                    message=f"Required phrase not found in README.md: '{phrase}'. "
                    "Add a non-affiliation statement and MIT license reference.",
                )
            )
    return violations


def _check_trademarks_notice(repo_root: Path) -> list[ComplianceViolation]:
    """Verify docs/trademarks.md exists and contains trademark notice."""
    trademarks = repo_root / TRADEMARKS_PATH
    if not trademarks.is_file():
        return [
            ComplianceViolation(
                check="trademarks_doc",
                path=TRADEMARKS_PATH,
                message="docs/trademarks.md is missing. "
                "Create it with a trademark attribution notice.",
            )
        ]

    content = trademarks.read_text(encoding="utf-8").lower()
    if TRADEMARKS_REQUIRED_PHRASE not in content:
        return [
            ComplianceViolation(
                check="trademarks_notice",
                path=TRADEMARKS_PATH,
                message=f"Trademark attribution phrase not found: "
                f"'{TRADEMARKS_REQUIRED_PHRASE}'. "
                "docs/trademarks.md must clarify that trademark usage is attribution-only.",
            )
        ]
    return []


def _check_changelog_provenance(repo_root: Path) -> list[ComplianceViolation]:
    """Verify upstream-intake CHANGELOG entries include provenance lines."""
    changelog = repo_root / CHANGELOG_PATH
    if not changelog.is_file():
        return []  # No changelog to check — not a violation itself

    lines = changelog.read_text(encoding="utf-8").splitlines()
    violations: list[ComplianceViolation] = []

    for i, line in enumerate(lines):
        line_lower = line.lower()
        if any(kw in line_lower for kw in UPSTREAM_INTAKE_KEYWORDS):
            # Look for a provenance line within the next PROVENANCE_LOOKAHEAD_LINES lines
            surrounding = "\n".join(lines[i : i + PROVENANCE_LOOKAHEAD_LINES])
            if not PROVENANCE_LINE_PATTERN.search(surrounding):
                violations.append(
                    ComplianceViolation(
                        check="changelog_provenance",
                        path=CHANGELOG_PATH,
                        message=(
                            f"Upstream-intake entry at line {i + 1} is missing a "
                            f"'Source PR:' provenance line. "
                            "Add 'Source PR: https://github.com/github/spec-kit/pull/<N>' "
                            "within the entry."
                        ),
                    )
                )

    return violations


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def run_compliance_checks(repo_root: Path) -> ComplianceResult:
    """Run all compliance checks and return a result object."""
    all_violations: list[ComplianceViolation] = []
    checks_run: list[str] = []

    steps = [
        ("license_present", _check_license_present),
        ("legal_compliance_doc_and_markers", _check_legal_compliance_markers),
        ("readme_phrases", _check_readme_phrases),
        ("trademarks_notice", _check_trademarks_notice),
        ("changelog_provenance", _check_changelog_provenance),
    ]

    for name, fn in steps:
        checks_run.append(name)
        all_violations.extend(fn(repo_root))

    return ComplianceResult(
        ok=not all_violations,
        checks_run=checks_run,
        violations=all_violations,
    )


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _as_repo_root(value: str | Path) -> Path:
    raw = str(value).strip()
    if not raw:
        raise ValueError("Repository root must be a non-empty path.")
    path = Path(raw).expanduser().resolve()
    if not path.is_dir():
        raise ValueError(f"Repository root does not exist or is not a directory: {path}")
    return path


def _cmd_check(args: argparse.Namespace) -> int:
    repo_root = _as_repo_root(args.repo_root)
    result = run_compliance_checks(repo_root)
    payload = result.to_dict()
    print(json.dumps(payload, indent=2, sort_keys=False))
    if not result.ok:
        sys.stderr.write(
            f"[compliance-checker] {len(result.violations)} violation(s) found.\n"
        )
    return 0 if result.ok else 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate legal/trademark/provenance compliance markers."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    check_parser = subparsers.add_parser(
        "check",
        help="Run all compliance checks against the repository.",
    )
    check_parser.add_argument(
        "--repo-root",
        default=".",
        help="Repository root to check (default: current directory).",
    )
    check_parser.set_defaults(handler=_cmd_check)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.handler(args)


if __name__ == "__main__":
    sys.exit(main())
