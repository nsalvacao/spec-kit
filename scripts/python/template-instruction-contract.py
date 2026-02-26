#!/usr/bin/env python3
"""Template/script instruction contract validator (issue #115)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_PATH = REPO_ROOT / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from specify_cli.template_instruction_contract import (
    INSTRUCTION_CONTRACT_MARKERS,
    INSTRUCTION_CONTRACT_TEMPLATES,
    validate_instruction_contract,
)


class InstructionContractError(ValueError):
    """Raised when validator configuration is invalid."""


def _as_repo_root(value: str | Path) -> Path:
    raw = str(value).strip()
    if not raw:
        raise InstructionContractError("Repository root must be a non-empty path.")
    path = Path(raw).expanduser().resolve()
    if not path.is_dir():
        raise InstructionContractError(f"Repository root does not exist: {path}")
    return path


def _cmd_validate(args: argparse.Namespace) -> int:
    repo_root = _as_repo_root(args.repo_root)
    errors = validate_instruction_contract(repo_root)
    payload = {
        "ok": not errors,
        "required_markers": list(INSTRUCTION_CONTRACT_MARKERS),
        "templates_checked": list(INSTRUCTION_CONTRACT_TEMPLATES),
        "errors": [error.to_dict() for error in errors],
    }
    print(json.dumps(payload, indent=2, sort_keys=False))
    return 1 if errors else 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate template/script instruction contract markers."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    validate_parser = subparsers.add_parser("validate", help="Validate instruction markers.")
    validate_parser.add_argument(
        "--repo-root",
        default=".",
        help="Repository root containing templates/commands.",
    )
    validate_parser.set_defaults(handler=_cmd_validate)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return int(args.handler(args))
    except InstructionContractError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    except (TypeError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
