#!/usr/bin/env python3
"""Programmatic orchestration contract helper (issue #113)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_PATH = REPO_ROOT / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from specify_cli.orchestration_contract import (
    build_orchestration_payload,
    normalize_orchestration_payload,
    validate_orchestration_payload,
)


class OrchestrationContractError(ValueError):
    """Raised when command input is invalid."""


def _load_json_file(path_value: str | Path, *, field_name: str) -> dict[str, Any]:
    path = Path(str(path_value).strip()).expanduser().resolve()
    if not path.is_file():
        raise OrchestrationContractError(f"{field_name} file does not exist: {path}")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise OrchestrationContractError(f"{field_name} file must be valid JSON: {path}") from exc
    if not isinstance(payload, dict):
        raise OrchestrationContractError(f"{field_name} payload must be a JSON object.")
    return payload


def _write_output(payload: dict[str, Any], output_path: str | None) -> None:
    serialized = json.dumps(payload, indent=2, sort_keys=False) + "\n"
    if output_path:
        path = Path(output_path).expanduser().resolve()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(serialized, encoding="utf-8")
    else:
        print(serialized, end="")


def _cmd_build(args: argparse.Namespace) -> int:
    raw_scope_gate = _load_json_file(args.scope_gate, field_name="scope-gate")
    payload = build_orchestration_payload(
        raw_scope_gate,
        channel=args.channel,
        request_id=args.request_id,
        timestamp=args.timestamp,
    )
    _write_output(payload.to_dict(), args.output)
    return 0


def _cmd_normalize(args: argparse.Namespace) -> int:
    raw_payload = _load_json_file(args.input, field_name="input")
    normalized = normalize_orchestration_payload(raw_payload, strict=args.strict)
    _write_output(normalized.to_dict(), args.output)
    return 0


def _cmd_validate(args: argparse.Namespace) -> int:
    raw_payload = _load_json_file(args.input, field_name="input")
    issues = validate_orchestration_payload(raw_payload, strict=args.strict)
    has_errors = any(issue["severity"] == "error" for issue in issues)
    result = {
        "ok": not has_errors,
        "issue_count": len(issues),
        "issues": issues,
    }
    _write_output(result, args.output)
    return 1 if has_errors else 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build/normalize/validate orchestration payload contract."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    build_parser = subparsers.add_parser(
        "build",
        help="Wrap scope-gate payload into orchestration envelope.",
    )
    build_parser.add_argument("--scope-gate", required=True, help="Path to scope-gate JSON payload.")
    build_parser.add_argument("--channel", default="api", help="Orchestration channel (api|cli|tui).")
    build_parser.add_argument("--request-id", help="Optional request UUID.")
    build_parser.add_argument("--timestamp", help="Optional ISO-8601 timestamp.")
    build_parser.add_argument("--output", help="Optional path to output JSON file.")
    build_parser.set_defaults(handler=_cmd_build)

    normalize_parser = subparsers.add_parser(
        "normalize",
        help="Normalize orchestration payload with compatibility fallbacks.",
    )
    normalize_parser.add_argument("--input", required=True, help="Path to input JSON payload.")
    normalize_parser.add_argument("--strict", action="store_true", help="Fail on contract errors.")
    normalize_parser.add_argument("--output", help="Optional path to output JSON file.")
    normalize_parser.set_defaults(handler=_cmd_normalize)

    validate_parser = subparsers.add_parser(
        "validate",
        help="Validate orchestration payload and print structured issues.",
    )
    validate_parser.add_argument("--input", required=True, help="Path to input JSON payload.")
    validate_parser.add_argument("--strict", action="store_true", help="Fail on contract errors.")
    validate_parser.add_argument("--output", help="Optional path to output JSON file.")
    validate_parser.set_defaults(handler=_cmd_validate)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return int(args.handler(args))
    except OrchestrationContractError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    except (TypeError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
