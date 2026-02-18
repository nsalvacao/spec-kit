"""Tests for Phase 0 integration in constitution template and agent docs (issues #11, #12).

Issue #11: constitution-template.md lacks Phase 0 integration guidance.
Issue #12: speckit.constitution.agent.md (and all agent docs) don't mention
           .spec-kit/ artifacts or clarify the Agent-as-executor model.
"""

from __future__ import annotations

from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).parent.parent
TEMPLATES_DIR = REPO_ROOT / "templates"
AGENTS_DIR = REPO_ROOT / ".github" / "agents"
COMMANDS_DIR = TEMPLATES_DIR / "commands"


# ---------------------------------------------------------------------------
# Issue #11 — constitution-template.md must reference Phase 0
# ---------------------------------------------------------------------------


class TestConstitutionTemplatePhase0(object):
    """Validate that templates/constitution-template.md guides users to
    carry Phase 0 insights into the constitution."""

    TEMPLATE = TEMPLATES_DIR / "constitution-template.md"

    def test_template_exists(self):
        assert self.TEMPLATE.exists(), "templates/constitution-template.md must exist"

    def test_template_references_spec_kit_dir(self):
        """Template must mention .spec-kit/ so users know to look there."""
        content = self.TEMPLATE.read_text(encoding="utf-8")
        assert ".spec-kit" in content, (
            "constitution-template.md must reference '.spec-kit/' to guide users "
            "to carry Phase 0 artifacts into the constitution."
        )

    def test_template_has_phase0_section_or_comment(self):
        """Template must contain a Phase 0 integration hint (section or comment)."""
        content = self.TEMPLATE.read_text(encoding="utf-8")
        has_phase0 = (
            "Phase 0" in content
            or "phase0" in content.lower()
            or "PHASE 0" in content
        )
        assert has_phase0, (
            "constitution-template.md must contain Phase 0 integration guidance "
            "(section, comment, or placeholder referencing Phase 0 artifacts)."
        )

    def test_template_guides_principles_from_phase0(self):
        """Template must explain that principles can be derived from Phase 0 canvas/ideas."""
        content = self.TEMPLATE.read_text(encoding="utf-8")
        # Should guide user to derive principles from Phase 0 artifacts
        has_guidance = any(
            term in content
            for term in ["canvas", "ideas_backlog", "ai_vision", "SCAMPER", "HMW"]
        )
        assert has_guidance, (
            "constitution-template.md must guide users to derive principles from "
            "Phase 0 artifacts (canvas, ideas_backlog, etc.)."
        )


# ---------------------------------------------------------------------------
# Issue #11 — constitution-template.md must also reference .ideas/ (Strategy Toolkit)
# ---------------------------------------------------------------------------


def test_constitution_template_references_ideas_dir():
    """constitution-template.md must mention .ideas/ (Strategy Toolkit artifacts)."""
    template = TEMPLATES_DIR / "constitution-template.md"
    content = template.read_text(encoding="utf-8")
    assert ".ideas" in content, (
        "constitution-template.md must reference '.ideas/' to guide users "
        "to use Strategy Toolkit artifacts when available."
    )


# ---------------------------------------------------------------------------
# Issue #12 — speckit.constitution.agent.md must reference .spec-kit/
# ---------------------------------------------------------------------------


@pytest.mark.skipif(
    not (AGENTS_DIR / "speckit.constitution.agent.md").exists(),
    reason=".github/agents/ is gitignored; skipped in CI (generated locally by specify init)",
)
class TestConstitutionAgentDocPhase0(object):
    """Validate that .github/agents/speckit.constitution.agent.md instructs
    the AI agent to discover and use .spec-kit/ Phase 0 artifacts."""

    AGENT_DOC = AGENTS_DIR / "speckit.constitution.agent.md"

    def test_agent_doc_exists(self):
        assert self.AGENT_DOC.exists(), (
            ".github/agents/speckit.constitution.agent.md must exist"
        )

    def test_agent_doc_references_spec_kit_dir(self):
        """Agent doc must instruct AI to look in .spec-kit/ for Phase 0 artifacts."""
        content = self.AGENT_DOC.read_text(encoding="utf-8")
        assert ".spec-kit" in content, (
            "speckit.constitution.agent.md must reference '.spec-kit/' so the AI "
            "agent discovers and uses Phase 0 artifacts."
        )

    def test_agent_doc_has_phase0_mention(self):
        """Agent doc must explicitly mention Phase 0."""
        content = self.AGENT_DOC.read_text(encoding="utf-8")
        assert "Phase 0" in content or "phase0" in content.lower(), (
            "speckit.constitution.agent.md must mention 'Phase 0' to guide AI."
        )

    def test_agent_doc_clarifies_executor_model(self):
        """Agent doc must clarify that the AI agent is the executor (not just advisor)."""
        content = self.AGENT_DOC.read_text(encoding="utf-8")
        # Look for executor model clarification
        has_executor = any(
            phrase in content
            for phrase in [
                "executor",
                "You are the executor",
                "write the file directly",
                "create the artifact",
                "create_file",
                "perform the task",
            ]
        )
        assert has_executor, (
            "speckit.constitution.agent.md must clarify that the AI is the executor: "
            "if a script is missing, the agent writes the artifact directly."
        )

    def test_agent_doc_references_ideas_dir(self):
        """Agent doc must also reference .ideas/ (Strategy Toolkit artifacts)."""
        content = self.AGENT_DOC.read_text(encoding="utf-8")
        assert ".ideas" in content, (
            "speckit.constitution.agent.md must reference '.ideas/' for Strategy "
            "Toolkit artifact discovery."
        )


# ---------------------------------------------------------------------------
# Issue #12 — ALL agent docs should mention .spec-kit/ (broad check)
# ---------------------------------------------------------------------------


PHASE0_AGENTS = [
    "speckit.constitution.agent.md",
    "speckit.specify.agent.md",
    "speckit.plan.agent.md",
    "speckit.tasks.agent.md",
]


@pytest.mark.parametrize("agent_filename", PHASE0_AGENTS)
def test_sdd_agent_docs_reference_spec_kit(agent_filename):
    """Core SDD agent docs must reference .spec-kit/ for Phase 0 context."""
    agent_doc = AGENTS_DIR / agent_filename
    if not agent_doc.exists():
        pytest.skip(f"{agent_filename} not found — skipping")
    content = agent_doc.read_text(encoding="utf-8")
    assert ".spec-kit" in content, (
        f"{agent_filename} must reference '.spec-kit/' so the AI agent "
        "can discover and use Phase 0 artifacts."
    )


# ---------------------------------------------------------------------------
# Canonical command templates must also have Phase 0 + .ideas/ context
# ---------------------------------------------------------------------------


PHASE0_COMMAND_TEMPLATES = [
    "constitution.md",
    "specify.md",
    "plan.md",
    "tasks.md",
]


@pytest.mark.parametrize("template_filename", PHASE0_COMMAND_TEMPLATES)
def test_command_templates_reference_spec_kit(template_filename):
    """Canonical command templates must reference .spec-kit/ for Phase 0 context."""
    template = COMMANDS_DIR / template_filename
    assert template.exists(), f"templates/commands/{template_filename} must exist"
    content = template.read_text(encoding="utf-8")
    assert ".spec-kit" in content, (
        f"templates/commands/{template_filename} must reference '.spec-kit/' "
        "so generated agent files guide AI to discover Phase 0 artifacts."
    )


@pytest.mark.parametrize("template_filename", PHASE0_COMMAND_TEMPLATES)
def test_command_templates_reference_ideas_dir(template_filename):
    """Canonical command templates must reference .ideas/ (Strategy Toolkit)."""
    template = COMMANDS_DIR / template_filename
    assert template.exists(), f"templates/commands/{template_filename} must exist"
    content = template.read_text(encoding="utf-8")
    assert ".ideas" in content, (
        f"templates/commands/{template_filename} must reference '.ideas/' "
        "so generated agent files guide AI to use Strategy Toolkit artifacts."
    )
