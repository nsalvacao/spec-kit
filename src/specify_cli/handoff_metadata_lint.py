"""Lint utilities for template handoff metadata and payload checks.

Issue: #116
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from .handoff_contract import normalize_handoff_metadata, validate_handoff_metadata


COMMAND_TEMPLATES_DIR = Path("templates/commands")
FRONTMATTER_RE = re.compile(r"^---[ \t]*\r?\n(.*?)\r?\n---[ \t]*(?:\r?\n|$)", re.DOTALL)
AGENT_STAGE_RE = re.compile(r"^speckit\.(?P<stage>[a-z0-9_-]+)$")

TEMPLATE_STAGE = {
    "specify.md": "specify",
    "clarify.md": "clarify",
    "plan.md": "plan",
    "tasks.md": "tasks",
}

NEXT_STAGE = {
    "specify": "plan",
    "clarify": "plan",
    "plan": "tasks",
    "tasks": "implement",
}


@dataclass(frozen=True)
class HandoffLintError:
    path: str
    message: str

    def to_dict(self) -> dict[str, str]:
        return {"path": self.path, "message": self.message}


def validate_template_handoffs(repo_root: Path) -> list[HandoffLintError]:
    """Validate handoff metadata blocks in command templates."""
    errors: list[HandoffLintError] = []
    root = repo_root.resolve()
    templates_root = (root / COMMAND_TEMPLATES_DIR).resolve()
    if not templates_root.exists():
        return [HandoffLintError(path=str(COMMAND_TEMPLATES_DIR), message="Command templates directory missing.")]

    for template_path in sorted(templates_root.glob("*.md")):
        if template_path.name not in TEMPLATE_STAGE:
            continue

        frontmatter = _parse_frontmatter(template_path)
        if not frontmatter:
            errors.append(HandoffLintError(path=str(template_path), message="Missing YAML frontmatter."))
            continue

        handoffs = frontmatter.get("handoffs")
        if not isinstance(handoffs, list) or not handoffs:
            errors.append(
                HandoffLintError(
                    path=str(template_path),
                    message="handoffs must be a non-empty list.",
                )
            )
            continue

        from_stage = TEMPLATE_STAGE[template_path.name]
        default_to_stage = NEXT_STAGE[from_stage]

        for index, handoff in enumerate(handoffs):
            relative_template = template_path.relative_to(root).as_posix()
            item_path = f"{relative_template}#handoffs[{index}]"
            if not isinstance(handoff, dict):
                errors.append(HandoffLintError(path=item_path, message="handoff entry must be an object."))
                continue

            label = handoff.get("label")
            agent = handoff.get("agent")
            prompt = handoff.get("prompt")
            send = handoff.get("send")

            if not isinstance(label, str) or not label.strip():
                errors.append(HandoffLintError(path=item_path, message="label must be a non-empty string."))
            if not isinstance(agent, str) or not agent.strip():
                errors.append(HandoffLintError(path=item_path, message="agent must be a non-empty string."))
                continue
            if not isinstance(prompt, str) or not prompt.strip():
                errors.append(HandoffLintError(path=item_path, message="prompt must be a non-empty string."))
            if send is not None and not isinstance(send, bool):
                errors.append(HandoffLintError(path=item_path, message="send must be boolean when provided."))

            match = AGENT_STAGE_RE.fullmatch(agent.strip())
            to_stage = match.group("stage") if match else default_to_stage
            if to_stage not in NEXT_STAGE and to_stage != "implement":
                to_stage = default_to_stage

            payload = {
                "from_stage": from_stage,
                "to_stage": to_stage,
                "handoff_owner": f"agent:{agent.strip()}",
                "next_action": prompt.strip() if isinstance(prompt, str) and prompt.strip() else "Continue workflow.",
            }
            issues = validate_handoff_metadata(payload, strict=False)
            errors.extend(
                HandoffLintError(path=item_path, message=issue["message"])
                for issue in issues
                if issue["severity"] == "error"
            )

    return errors


def validate_payload_file(payload_path: Path, *, strict: bool = False) -> tuple[dict[str, Any], int]:
    """Validate handoff payload file and return normalized payload + exit code."""
    raw = json.loads(payload_path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError("Payload file must contain a JSON object.")

    issues = validate_handoff_metadata(raw, strict=strict)
    normalized = normalize_handoff_metadata(raw, strict=False).to_dict()
    normalized["contract_issues"] = issues
    has_errors = any(issue["severity"] == "error" for issue in issues)
    return normalized, 1 if has_errors else 0


def _parse_frontmatter(path: Path) -> dict[str, Any]:
    content = path.read_text(encoding="utf-8")
    match = FRONTMATTER_RE.match(content)
    if not match:
        return {}
    parsed = yaml.safe_load(match.group(1)) or {}
    return parsed if isinstance(parsed, dict) else {}
