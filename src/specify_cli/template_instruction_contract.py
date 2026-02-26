"""Template instruction contract validation helpers.

Issue: #115
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


INSTRUCTION_CONTRACT_MARKERS = (
    "instruction-contract:options",
    "instruction-contract:recommended-default",
    "instruction-contract:risk-confirmation",
    "instruction-contract:canonical-write-paths",
    "instruction-contract:machine-readable-output",
)

INSTRUCTION_CONTRACT_TEMPLATES = (
    "templates/commands/specify.md",
    "templates/commands/clarify.md",
    "templates/commands/plan.md",
    "templates/commands/tasks.md",
)


@dataclass(frozen=True)
class InstructionContractError:
    template: str
    missing_markers: list[str]

    def to_dict(self) -> dict[str, object]:
        return {"template": self.template, "missing_markers": self.missing_markers}


def validate_instruction_contract(
    repo_root: Path,
    *,
    template_paths: Iterable[str] = INSTRUCTION_CONTRACT_TEMPLATES,
    required_markers: Iterable[str] = INSTRUCTION_CONTRACT_MARKERS,
) -> list[InstructionContractError]:
    """Validate instruction-contract markers in template command files."""
    errors: list[InstructionContractError] = []
    normalized_markers = tuple(required_markers)

    for rel_path in template_paths:
        absolute_path = (repo_root / rel_path).resolve()
        if not absolute_path.exists():
            errors.append(
                InstructionContractError(
                    template=rel_path,
                    missing_markers=["<file-missing>"],
                )
            )
            continue

        content = absolute_path.read_text(encoding="utf-8")
        missing = [marker for marker in normalized_markers if marker not in content]
        if missing:
            errors.append(
                InstructionContractError(
                    template=rel_path,
                    missing_markers=missing,
                )
            )

    return errors
