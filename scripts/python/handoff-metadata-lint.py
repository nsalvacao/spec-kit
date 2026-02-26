#!/usr/bin/env python3
"""Handoff metadata schema/lint gate (issue #116)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

MAX_INPUT_BYTES = 1_048_576  # 1 MiB
MAX_JSON_DEPTH = 64


def _bootstrap_src_path() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    src_path = (repo_root / "src").resolve()
    package_dir = src_path / "specify_cli"

    if not src_path.is_dir() or not package_dir.is_dir():
        raise RuntimeError("Unable to locate expected source package at 'src/specify_cli'.")
    if repo_root not in src_path.parents:
        raise RuntimeError("Resolved source path escapes repository root.")

    src_path_str = str(src_path)
    if src_path_str not in sys.path:
        sys.path.insert(0, src_path_str)


_bootstrap_src_path()

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
    size_bytes = path.stat().st_size
    if size_bytes > MAX_INPUT_BYTES:
        raise HandoffLintCommandError(
            f"Payload file is too large ({size_bytes} bytes). "
            f"Limit is {MAX_INPUT_BYTES} bytes."
        )
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
    _ensure_json_depth(payload_file)
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


def _ensure_json_depth(payload_file: Path) -> None:
    try:
        raw = json.loads(payload_file.read_text(encoding="utf-8"))
    except UnicodeDecodeError as exc:
        raise HandoffLintCommandError(f"Payload file must be UTF-8 text JSON: {payload_file}") from exc
    except json.JSONDecodeError as exc:
        raise HandoffLintCommandError(f"Payload file must be valid JSON: {payload_file}") from exc
    if not isinstance(raw, dict):
        raise HandoffLintCommandError("Payload file must contain a JSON object.")

    def depth(value: object, level: int = 0) -> int:
        if isinstance(value, dict):
            if not value:
                return level
            return max(depth(v, level + 1) for v in value.values())
        if isinstance(value, list):
            if not value:
                return level
            return max(depth(v, level + 1) for v in value)
        return level

    payload_depth = depth(raw)
    if payload_depth > MAX_JSON_DEPTH:
        raise HandoffLintCommandError(
            f"Payload JSON nesting depth {payload_depth} exceeds limit {MAX_JSON_DEPTH}."
        )


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return int(args.handler(args))
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    except HandoffLintCommandError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    except (OSError, TypeError, ValueError, json.JSONDecodeError) as exc:
        print(str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
