"""Tests for handoff metadata protocol (issue #14).

Validates that all Phase 0 → SDD artifact templates carry the required
YAML frontmatter fields defined in docs/handoff-metadata.md.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Optional

import pytest
import yaml

REPO_ROOT = Path(__file__).parent.parent
TEMPLATES = REPO_ROOT / "templates"

# Artifacts in chain order: (file, required_derived_from, required_enables)
PHASE0_CHAIN = [
    (
        "ideas-backlog-template.md",
        None,  # derived_from must be null (root)
        ".spec-kit/idea_selection.md",
    ),
    (
        "idea-selection-template.md",
        ".spec-kit/ideas_backlog.md",
        ".spec-kit/ai_vision_canvas.md",
    ),
    (
        "ai-vision-canvas-template.md",
        ".spec-kit/idea_selection.md",
        ".spec-kit/vision_brief.md",
    ),
    (
        "vision-brief-template.md",
        ".spec-kit/ai_vision_canvas.md",
        ".spec-kit/g0_validation_report.md",
    ),
    (
        "g0-validation-report-template.md",
        ".spec-kit/vision_brief.md",
        ".specify/spec.md",
    ),
]

SDD_CHAIN = [
    (
        "spec-template.md",
        ".spec-kit/g0_validation_report.md",
        None,  # enables must be null (leaf)
    ),
]

REQUIRED_FIELDS = ["artifact", "phase", "schema_version", "generated", "derived_from", "enables"]


def _parse_frontmatter(path: Path) -> dict:
    """Extract YAML frontmatter from a markdown file.

    Requires the frontmatter to start at the very first line of the file
    (the opening ``---`` must be on line 1). Uses a non-greedy match so
    any additional ``---`` dividers inside the body are ignored.
    """
    content = path.read_text(encoding="utf-8")
    # Strict: opening --- must be at byte 0, closing --- on its own line
    match = re.match(r"^---[ \t]*\r?\n(.*?)\r?\n---[ \t]*(?:\r?\n|$)", content, re.DOTALL)
    if not match:
        return {}
    return yaml.safe_load(match.group(1)) or {}


def _template_path(filename: str) -> Path:
    return TEMPLATES / filename


class TestRequiredFields:
    """All Phase 0 templates must have the full set of required frontmatter fields."""

    @pytest.mark.parametrize("filename,_,__", PHASE0_CHAIN + SDD_CHAIN)
    def test_has_all_required_fields(self, filename, _, __):
        fm = _parse_frontmatter(_template_path(filename))
        missing = [f for f in REQUIRED_FIELDS if f not in fm]
        assert not missing, f"{filename}: missing frontmatter fields: {missing}"

    @pytest.mark.parametrize("filename,_,__", PHASE0_CHAIN + SDD_CHAIN)
    def test_schema_version_is_1_0(self, filename, _, __):
        fm = _parse_frontmatter(_template_path(filename))
        assert fm.get("schema_version") == "1.0", (
            f"{filename}: schema_version should be '1.0', got {fm.get('schema_version')!r}"
        )

    @pytest.mark.parametrize("filename,_,__", PHASE0_CHAIN + SDD_CHAIN)
    def test_artifact_field_is_snake_case(self, filename, _, __):
        fm = _parse_frontmatter(_template_path(filename))
        artifact = fm.get("artifact", "")
        assert re.match(r"^[a-z][a-z0-9_]*$", artifact), (
            f"{filename}: artifact '{artifact}' must be snake_case"
        )


class TestHandoffChain:
    """Templates must declare correct derived_from/enables links."""

    @pytest.mark.parametrize("filename,expected_derived,expected_enables", PHASE0_CHAIN + SDD_CHAIN)
    def test_derived_from(self, filename, expected_derived, expected_enables):
        fm = _parse_frontmatter(_template_path(filename))
        actual = fm.get("derived_from")
        assert actual == expected_derived, (
            f"{filename}: derived_from expected {expected_derived!r}, got {actual!r}"
        )

    @pytest.mark.parametrize("filename,expected_derived,expected_enables", PHASE0_CHAIN + SDD_CHAIN)
    def test_enables(self, filename, expected_derived, expected_enables):
        fm = _parse_frontmatter(_template_path(filename))
        actual = fm.get("enables")
        assert actual == expected_enables, (
            f"{filename}: enables expected {expected_enables!r}, got {actual!r}"
        )


class TestChainCompleteness:
    """Verify the full chain forms a connected graph with no gaps."""

    def test_chain_has_single_root(self):
        """Exactly one artifact should have derived_from=null."""
        roots = [f for f, d, _ in PHASE0_CHAIN if d is None]
        assert len(roots) == 1, f"Expected 1 root, got {len(roots)}: {roots}"

    def test_chain_has_single_leaf(self):
        """Exactly one artifact should have enables=null."""
        leaves = [f for f, _, e in SDD_CHAIN if e is None]
        assert len(leaves) == 1, f"Expected 1 leaf, got {len(leaves)}: {leaves}"

    def test_enables_matches_next_derived_from(self):
        """Each artifact's enables must be the same path that the next artifact's derived_from references.

        Example: ideas_backlog.enables='.spec-kit/idea_selection.md'
                 idea_selection.derived_from='.spec-kit/ideas_backlog.md'
        These are *different* paths pointing in opposite directions, so we verify
        that the filenames are consistent (A.enables contains next artifact name,
        B.derived_from contains current artifact name).
        """
        full_chain = PHASE0_CHAIN + SDD_CHAIN
        for i in range(len(full_chain) - 1):
            current_file, _, current_enables = full_chain[i]
            next_file, next_derived, _ = full_chain[i + 1]
            # current.enables must not be None (except the last)
            assert current_enables is not None, (
                f"{current_file}: enables=None but it's not the last artifact"
            )
            # next.derived_from must not be None (except the first)
            assert next_derived is not None, (
                f"{next_file}: derived_from=None but it's not the first artifact"
            )
            # The path that current enables must exist (the next artifact's output path)
            # and the next artifact's derived_from must point back to current's output path
            # We validate they form a consistent pair by checking path components
            current_artifact = _parse_frontmatter(_template_path(current_file)).get("artifact", "")
            next_artifact = _parse_frontmatter(_template_path(next_file)).get("artifact", "")
            # next.derived_from should reference current artifact by name
            assert current_artifact in next_derived, (
                f"Chain break: {next_file}.derived_from={next_derived!r} "
                f"does not reference current artifact '{current_artifact}'"
            )
            # current.enables should reference next artifact by name
            assert next_artifact in current_enables, (
                f"Chain break: {current_file}.enables={current_enables!r} "
                f"does not reference next artifact '{next_artifact}'"
            )

    def test_all_template_files_exist(self):
        """All referenced template files must exist on disk."""
        for filename, _, _ in PHASE0_CHAIN + SDD_CHAIN:
            path = _template_path(filename)
            assert path.exists(), f"Template not found: {path}"


class TestDocumentationExists:
    """The handoff protocol must be documented."""

    def test_handoff_metadata_doc_exists(self):
        doc = REPO_ROOT / "docs" / "handoff-metadata.md"
        assert doc.exists(), "docs/handoff-metadata.md missing"

    def test_handoff_metadata_doc_has_schema(self):
        doc = (REPO_ROOT / "docs" / "handoff-metadata.md").read_text()
        assert "schema_version" in doc
        assert "derived_from" in doc
        assert "enables" in doc


class TestNegativeCases:
    """_parse_frontmatter must handle malformed or missing frontmatter gracefully."""

    def test_no_frontmatter_returns_empty_dict(self, tmp_path: Path) -> None:
        f = tmp_path / "no-fm.md"
        f.write_text("# Just a heading\n\nNo frontmatter here.\n")
        assert _parse_frontmatter(f) == {}

    def test_frontmatter_not_at_start_returns_empty_dict(self, tmp_path: Path) -> None:
        f = tmp_path / "late-fm.md"
        f.write_text("Some preamble\n---\nkey: value\n---\n")
        assert _parse_frontmatter(f) == {}

    def test_unclosed_frontmatter_returns_empty_dict(self, tmp_path: Path) -> None:
        f = tmp_path / "unclosed-fm.md"
        f.write_text("---\nkey: value\n# No closing delimiter\n")
        assert _parse_frontmatter(f) == {}

    def test_empty_frontmatter_returns_empty_dict(self, tmp_path: Path) -> None:
        f = tmp_path / "empty-fm.md"
        f.write_text("---\n---\n# Body\n")
        assert _parse_frontmatter(f) == {}

    def test_missing_required_field_is_detected(self, tmp_path: Path) -> None:
        """A template missing a required field should fail the required-fields check."""
        f = tmp_path / "partial-fm.md"
        # Missing 'enables' and 'derived_from'
        f.write_text("---\nartifact: test\nphase: ideate\nschema_version: \"1.0\"\ngenerated: 2024-01-01T00:00:00Z\n---\n# Body\n")
        fm = _parse_frontmatter(f)
        missing = [field for field in REQUIRED_FIELDS if field not in fm]
        assert "enables" in missing
        assert "derived_from" in missing
