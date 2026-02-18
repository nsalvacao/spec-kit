"""Tests for validate-constitution.sh (issue #20).

Tests cover:
- Automated checks A1-A8 (non-waivable)
- Manual checks Q1-Q4, P1-P2 (waivable)
- Waiver Mechanism: --waive flag with justification
- RESULT: PASS / PASS WITH WAIVER / FAIL output
"""

import re
import subprocess
import tempfile
from pathlib import Path

import pytest

SCRIPT_DIR = Path(__file__).parent.parent / "scripts" / "bash"
SCRIPT = SCRIPT_DIR / "validate-constitution.sh"

# A minimal valid constitution that passes all automated checks
MINIMAL_VALID_CONSTITUTION = """# TestProject Constitution

## Core Principles

### I. Library-First

Every feature starts as a standalone library. Libraries must be self-contained,
independently testable, and documented. Clear purpose required.

### II. Test-First (NON-NEGOTIABLE)

TDD mandatory: Tests written, user approved, tests fail, then implement.
Red-Green-Refactor cycle strictly enforced for all production code.

### III. Observability

Text I/O ensures debuggability. Structured logging required for all services.
Metrics exposed via Prometheus-compatible endpoints.

## Development Workflow

Code review required for all PRs. No self-merging. Two approvals for main branch.
All changes must include passing tests and updated documentation.

**Version**: 1.0.0 | **Ratified**: 2025-06-13 | **Last Amended**: 2025-07-16

## Governance

This constitution supersedes all other practices. Amendments require documentation,
approval from two maintainers, and a migration plan. All PRs must verify compliance.
Ratification process: propose → review → vote → ratify.
"""

# Constitution with Phase 0 references (passes P1 too)
CONSTITUTION_WITH_PHASE0 = MINIMAL_VALID_CONSTITUTION.replace(
    "## Core Principles",
    "<!-- Derived from .spec-kit/ai_vision_canvas.md and .spec-kit/ideas_backlog.md -->\n## Core Principles",
)

# Constitution still containing the template Phase 0 comment block (Q1 fails)
CONSTITUTION_WITH_PHASE0_BLOCK = MINIMAL_VALID_CONSTITUTION.replace(
    "# TestProject Constitution",
    "# TestProject Constitution\n\n<!-- PHASE 0 INTEGRATION CHECK\n     Check .spec-kit/ artifacts here.\n-->\n",
)

# Constitution missing ## Core Principles
CONSTITUTION_MISSING_PRINCIPLES = MINIMAL_VALID_CONSTITUTION.replace(
    "## Core Principles", "## Key Principles"
)

# Constitution missing ## Governance
CONSTITUTION_MISSING_GOVERNANCE = MINIMAL_VALID_CONSTITUTION.replace(
    "## Governance", "## Rules"
)

# Constitution missing Version:
CONSTITUTION_MISSING_VERSION = MINIMAL_VALID_CONSTITUTION.replace("**Version**: 1.0.0 | ", "")

# Constitution missing Ratified:
CONSTITUTION_MISSING_RATIFIED = MINIMAL_VALID_CONSTITUTION.replace(
    " | **Ratified**: 2025-06-13", ""
)

# Constitution with unfilled placeholder
CONSTITUTION_WITH_PLACEHOLDER = MINIMAL_VALID_CONSTITUTION.replace(
    "TestProject", "[PROJECT_NAME]"
)

# Constitution with only 2 principles
CONSTITUTION_FEW_PRINCIPLES = re.sub(
    r"\n### III\. Observability.*?## Development",
    "\n## Development",
    MINIMAL_VALID_CONSTITUTION,
    flags=re.DOTALL,
)

# Constitution with empty Governance section
CONSTITUTION_EMPTY_GOVERNANCE = MINIMAL_VALID_CONSTITUTION.replace(
    """## Governance

This constitution supersedes all other practices. Amendments require documentation,
approval from two maintainers, and a migration plan. All PRs must verify compliance.
Ratification process: propose → review → vote → ratify.""",
    "## Governance\n\n<!-- governance content here -->",
)


@pytest.fixture()
def workdir(tmp_path):
    """Provide a clean temporary directory."""
    return tmp_path


@pytest.fixture()
def valid_constitution(workdir):
    """Write a valid constitution and return its path."""
    path = workdir / "constitution.md"
    path.write_text(MINIMAL_VALID_CONSTITUTION)
    return path


def run_script(workdir: Path, file_path: Path, *extra_args: str) -> subprocess.CompletedProcess:
    """Run validate-constitution.sh from the given workdir."""
    cmd = ["bash", str(SCRIPT), str(file_path), *extra_args]
    return subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        cwd=str(workdir),
    )


# ──────────────────────────────────────────────────────────────
# Automated Check Tests
# ──────────────────────────────────────────────────────────────


class TestAutomatedChecks:
    def test_a1_file_missing(self, workdir):
        result = run_script(workdir, workdir / "missing.md")
        assert result.returncode == 1
        assert "A1" in result.stderr

    def test_a1_file_present(self, workdir, valid_constitution):
        result = run_script(workdir, valid_constitution)
        assert "PASS [A1]" in result.stdout

    def test_a2_file_too_short(self, workdir):
        tiny = workdir / "tiny.md"
        tiny.write_text("# Short\n\n## Core Principles\n\nHello\n")
        result = run_script(workdir, tiny)
        assert result.returncode == 1
        assert "A2" in result.stderr

    def test_a3_missing_core_principles(self, workdir):
        path = workdir / "c.md"
        path.write_text(CONSTITUTION_MISSING_PRINCIPLES)
        result = run_script(workdir, path)
        assert result.returncode == 1
        assert "A3" in result.stderr

    def test_a4_missing_governance(self, workdir):
        path = workdir / "c.md"
        path.write_text(CONSTITUTION_MISSING_GOVERNANCE)
        result = run_script(workdir, path)
        assert result.returncode == 1
        assert "A4" in result.stderr

    def test_a5_missing_version(self, workdir):
        path = workdir / "c.md"
        path.write_text(CONSTITUTION_MISSING_VERSION)
        result = run_script(workdir, path)
        assert result.returncode == 1
        assert "A5" in result.stderr

    def test_a5_missing_ratified(self, workdir):
        path = workdir / "c.md"
        path.write_text(CONSTITUTION_MISSING_RATIFIED)
        result = run_script(workdir, path)
        assert result.returncode == 1
        assert "A5" in result.stderr

    def test_a6_unfilled_placeholder(self, workdir):
        path = workdir / "c.md"
        path.write_text(CONSTITUTION_WITH_PLACEHOLDER)
        result = run_script(workdir, path)
        assert result.returncode == 1
        assert "A6" in result.stderr

    def test_a7_too_few_principles(self, workdir):
        path = workdir / "c.md"
        path.write_text(CONSTITUTION_FEW_PRINCIPLES)
        result = run_script(workdir, path)
        assert result.returncode == 1
        assert "A7" in result.stderr

    def test_a8_empty_governance(self, workdir):
        path = workdir / "c.md"
        path.write_text(CONSTITUTION_EMPTY_GOVERNANCE)
        result = run_script(workdir, path)
        assert result.returncode == 1
        assert "A8" in result.stderr

    def test_full_valid_constitution_passes_automated(self, workdir, valid_constitution):
        result = run_script(
            workdir, valid_constitution,
            "--waive", "P1", "Phase 0 not used; principles from team conventions",
        )
        assert result.returncode == 0
        for check in ("A1", "A2", "A3", "A4", "A5", "A6", "A7", "A8"):
            assert f"PASS [{check}]" in result.stdout


# ──────────────────────────────────────────────────────────────
# Result Output Tests
# ──────────────────────────────────────────────────────────────


class TestResultOutput:
    def test_pass_result_on_valid_constitution(self, workdir):
        """A well-filled constitution (with Phase 0 refs) should give PASS."""
        path = workdir / "c.md"
        path.write_text(CONSTITUTION_WITH_PHASE0)
        result = run_script(workdir, path)
        # May still have Q1 warn (no phase0 block to complain about) but P1 passes
        assert result.returncode == 0

    def test_fail_result_on_missing_file(self, workdir):
        result = run_script(workdir, workdir / "none.md")
        assert result.returncode == 1
        assert "A1" in result.stderr

    def test_fail_result_propagates_when_manual_unresolved(self, workdir, valid_constitution):
        """Q1 fails (Phase 0 block present) and no waiver → FAIL."""
        path = workdir / "c.md"
        path.write_text(CONSTITUTION_WITH_PHASE0_BLOCK)
        result = run_script(workdir, path)
        assert result.returncode == 1
        assert "RESULT: FAIL" in result.stdout


# ──────────────────────────────────────────────────────────────
# Waiver Mechanism Tests
# ──────────────────────────────────────────────────────────────


class TestWaiverMechanism:
    def test_waive_q1_resolves_failure(self, workdir):
        """Waiving Q1 should turn a FAIL into PASS WITH WAIVER."""
        path = workdir / "c.md"
        path.write_text(CONSTITUTION_WITH_PHASE0_BLOCK)
        # Also need P1 waived since no .spec-kit/ refs
        result = run_script(
            workdir,
            path,
            "--waive", "Q1", "Phase 0 comment left for documentation purposes",
            "--waive", "P1", "Phase 0 not used; principles from team conventions",
        )
        assert result.returncode == 0

    def test_waive_shows_waived_label(self, workdir):
        """When a check is waived, output should show WAIVED [criterion]."""
        path = workdir / "c.md"
        path.write_text(CONSTITUTION_WITH_PHASE0_BLOCK)
        result = run_script(
            workdir,
            path,
            "--waive", "Q1", "Kept for new team member reference",
            "--waive", "P1", "No Phase 0 used",
        )
        assert "WAIVED [Q1]" in result.stdout

    def test_waive_with_justification_in_output(self, workdir):
        """Waiver justification text should appear in the output."""
        path = workdir / "c.md"
        # Strip P1-related tokens to force P1 to fail, then waive it
        brief_no_p1 = re.sub(
            r"(\.spec-kit/|ai_vision_canvas|ideas_backlog|idea_selection|g0_validation|vision_brief)",
            "REMOVED",
            MINIMAL_VALID_CONSTITUTION,
            flags=re.IGNORECASE,
        )
        path.write_text(brief_no_p1)
        result = run_script(
            workdir,
            path,
            "--waive", "P1", "Phase 0 artifacts stored externally",
            "--waive", "Q1", "No phase0 block present",
        )
        assert "Phase 0 artifacts stored externally" in result.stdout

    def test_pass_with_waiver_result_when_waivers_applied(self, workdir):
        """PASS WITH WAIVER only appears when a check fails but is waived."""
        # Strip Phase 0 artifact refs to force P1 to fail
        no_p1_refs = re.sub(
            r"(\.spec-kit/|ai_vision_canvas|ideas_backlog|idea_selection|g0_validation|vision_brief)",
            "REMOVED",
            MINIMAL_VALID_CONSTITUTION,
            flags=re.IGNORECASE,
        )
        path = workdir / "c.md"
        path.write_text(no_p1_refs)
        result = run_script(workdir, path, "--waive", "P1", "Phase 0 not used")
        assert result.returncode == 0
        assert "PASS WITH WAIVER" in result.stdout

    def test_automated_checks_not_waivable(self, workdir):
        """Even with --waive A1, missing file should still fail."""
        result = run_script(
            workdir,
            workdir / "missing.md",
            "--waive", "A1", "We know the file is missing",
        )
        assert result.returncode == 1
        assert "A1" in result.stderr
