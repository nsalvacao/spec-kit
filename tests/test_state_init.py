"""Tests for state-init.sh and state-init.ps1 utilities (issue #23).

Tests cover:
- Creates .spec-kit/ directory when missing
- Creates .spec-kit/approvals/ directory (new requirement - issue #23)
- Initializes state.yaml with correct content
- Idempotent: safe to run twice (existing state.yaml preserved)
- Existing state.yaml is not overwritten
"""

import subprocess
import tempfile
import os
from pathlib import Path

import pytest

SCRIPT_DIR = Path(__file__).parent.parent / "scripts" / "bash"
STATE_INIT_SCRIPT = SCRIPT_DIR / "state-init.sh"

EXPECTED_STATE_KEYS = [
    "workflow_version",
    "current_phase",
    "phases_completed",
    "phases_in_progress",
    "artifacts",
    "profile",
    "violations",
]


def run_script(cwd: Path) -> subprocess.CompletedProcess:
    """Run state-init.sh in the given working directory."""
    return subprocess.run(
        [str(STATE_INIT_SCRIPT)],
        cwd=str(cwd),
        capture_output=True,
        text=True,
    )


class TestStateInitScript:
    """Verify state-init.sh creates required directory structure."""

    def test_script_exists(self) -> None:
        """Script file must exist and be executable."""
        assert STATE_INIT_SCRIPT.exists(), f"Script not found: {STATE_INIT_SCRIPT}"
        assert os.access(STATE_INIT_SCRIPT, os.X_OK), "Script is not executable"

    def test_creates_spec_kit_dir(self) -> None:
        """state-init.sh must create .spec-kit/ when it does not exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            result = run_script(tmp)
            assert result.returncode == 0, result.stderr
            assert (tmp / ".spec-kit").is_dir()

    def test_creates_approvals_dir(self) -> None:
        """state-init.sh must create .spec-kit/approvals/ directory (issue #23)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            result = run_script(tmp)
            assert result.returncode == 0, result.stderr
            assert (tmp / ".spec-kit" / "approvals").is_dir(), (
                ".spec-kit/approvals/ was not created by state-init.sh"
            )

    def test_creates_state_yaml(self) -> None:
        """state-init.sh must create .spec-kit/state.yaml."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            result = run_script(tmp)
            assert result.returncode == 0, result.stderr
            state_file = tmp / ".spec-kit" / "state.yaml"
            assert state_file.exists()

    def test_state_yaml_has_required_keys(self) -> None:
        """state.yaml must contain all required top-level keys."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            run_script(tmp)
            content = (tmp / ".spec-kit" / "state.yaml").read_text()
            for key in EXPECTED_STATE_KEYS:
                assert key in content, f"Missing key '{key}' in state.yaml"

    def test_idempotent_state_yaml(self) -> None:
        """Running twice must not overwrite an existing state.yaml."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            run_script(tmp)
            # Modify state.yaml to a sentinel value
            state_file = tmp / ".spec-kit" / "state.yaml"
            original = state_file.read_text()
            state_file.write_text("# modified\n" + original)
            modified_content = state_file.read_text()
            # Run again
            result = run_script(tmp)
            assert result.returncode == 0, result.stderr
            assert state_file.read_text() == modified_content, (
                "state.yaml was overwritten on second run"
            )

    def test_idempotent_approvals_dir(self) -> None:
        """Running twice must not fail if .spec-kit/approvals/ already exists."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            run_script(tmp)
            # Second run — should succeed without error
            result = run_script(tmp)
            assert result.returncode == 0, result.stderr
            assert (tmp / ".spec-kit" / "approvals").is_dir()

    def test_output_on_first_run(self) -> None:
        """Script must print 'state.yaml initialized' on first run."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = run_script(Path(tmpdir))
            assert "initialized" in result.stdout

    def test_output_on_second_run(self) -> None:
        """Script must print 'state.yaml already exists' on second run."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            run_script(tmp)
            result = run_script(tmp)
            assert "already exists" in result.stdout
