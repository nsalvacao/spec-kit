#!/usr/bin/env python3
"""Handoff metadata schema/lint gate (issue #116)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_PATH = REPO_ROOT / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from specify_cli.handoff_metadata_lint import (
    validate_payload_file,
    validate_template_handoffs,
)


class HandoffLintCommandError(ValueError):
    """Raised when lint command input is invalid."""


def _as_repo_root(value: str | Path) -> Path:
    raw = str(value).strip()
    if not raw:
        raise HandoffLintCommandError("Repository root must be a non-empty path.")
    path = Path(raw).expanduser().resolve()
    if not path.is_dir():
        raise HandoffLintCommandError(f"Repository root does not exist: {path}")
    return path


def _as_payload_file(value: str | Path) -> Path:
    raw = str(value).strip()
    if not raw:
        raise HandoffLintCommandError("Payload file must be a non-empty path.")
    path = Path(raw).expanduser().resolve()
    if not path.is_file():
        raise HandoffLintCommandError(f"Payload file does not exist: {path}")
    return path


def _write_payload(payload: dict[str, object], output: str | None) -> None:
    serialized = json.dumps(payload, indent=2, sort_keys=False) + "\n"
    if output:
        path = Path(output).expanduser().resolve()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(serialized, encoding="utf-8")
    else:
        print(serialized, end="")


def _cmd_templates(args: argparse.Namespace) -> int:
    repo_root = _as_repo_root(args.repo_root)
    errors = validate_template_handoffs(repo_root)
    payload = {
        "ok": not errors,
        "error_count": len(errors),
        "errors": [error.to_dict() for error in errors],
    }
    _write_payload(payload, args.output)
    return 1 if errors else 0


def _cmd_payload(args: argparse.Namespace) -> int:
    payload_file = _as_payload_file(args.input)
    normalized, exit_code = validate_payload_file(payload_file, strict=args.strict)
    result = {
        "ok": exit_code == 0,
        "normalized_payload": normalized,
    }
    _write_payload(result, args.output)
    return exit_code


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate handoff metadata for templates and payload files."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    templates_parser = subparsers.add_parser(
        "templates",
        help="Validate handoff metadata declarations in command templates.",
    )
    templates_parser.add_argument(
        "--repo-root",
        default=".",
        help="Repository root path.",
    )
    templates_parser.add_argument("--output", help="Optional path to output JSON file.")
    templates_parser.set_defaults(handler=_cmd_templates)

    payload_parser = subparsers.add_parser(
        "payload",
        help="Validate and normalize a handoff payload JSON file.",
    )
    payload_parser.add_argument("--input", required=True, help="Path to JSON payload.")
    payload_parser.add_argument("--strict", action="store_true", help="Fail fast on validation errors.")
    payload_parser.add_argument("--output", help="Optional path to output JSON file.")
    payload_parser.set_defaults(handler=_cmd_payload)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return int(args.handler(args))
    except HandoffLintCommandError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    except (TypeError, ValueError, json.JSONDecodeError) as exc:
        print(str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
