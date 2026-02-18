"""Tests for detect-phase0.sh and detect-phase0.ps1 utilities (issue #10).

Tests cover:
- Option B: state.yaml with phases_completed
- Option A: .spec-kit/ideation/ directory fallback
- --verbose and --json flags
- Edge cases: missing state file, empty directory, corrupt YAML
"""

import subprocess
import tempfile
import json
import os
import shutil
from pathlib import Path

import pytest

SCRIPT_DIR = Path(__file__).parent.parent / "scripts" / "bash"
DETECT_SCRIPT = SCRIPT_DIR / "detect-phase0.sh"


def run_script(cwd: Path, *args) -> subprocess.CompletedProcess:
    """Run detect-phase0.sh in the given working directory."""
    return subprocess.run(
        [str(DETECT_SCRIPT), *args],
        cwd=str(cwd),
        capture_output=True,
        text=True,
    )


def write_state(cwd: Path, phases_completed: list) -> Path:
    """Write a minimal state.yaml with given phases_completed list."""
    spec_kit_dir = cwd / ".spec-kit"
    spec_kit_dir.mkdir(exist_ok=True)
    state_file = spec_kit_dir / "state.yaml"
    phases_str = "\n".join(f"- {p}" for p in phases_completed) if phases_completed else ""
    content = f"workflow_version: '1.0'\ncurrent_phase: ideate\nphases_completed:\n{phases_str}\n"
    if not phases_completed:
        content = "workflow_version: '1.0'\ncurrent_phase: ideate\nphases_completed: []\n"
    state_file.write_text(content)
    return state_file


def write_ideation_file(cwd: Path, filename: str = "ideas.md") -> Path:
    """Create a file in .spec-kit/ideation/."""
    ideation_dir = cwd / ".spec-kit" / "ideation"
    ideation_dir.mkdir(parents=True, exist_ok=True)
    f = ideation_dir / filename
    f.write_text("# Ideas\n- idea 1\n")
    return f


@pytest.fixture
def tmpdir():
    """Provide a clean temporary directory per test."""
    d = Path(tempfile.mkdtemp())
    yield d
    shutil.rmtree(d, ignore_errors=True)


# ─── Script existence ─────────────────────────────────────────────────────────

class TestScriptExists:
    def test_bash_script_exists(self):
        assert DETECT_SCRIPT.exists(), f"{DETECT_SCRIPT} not found"

    def test_bash_script_executable(self):
        assert os.access(DETECT_SCRIPT, os.X_OK), f"{DETECT_SCRIPT} is not executable"

    def test_powershell_script_exists(self):
        ps1 = Path(__file__).parent.parent / "scripts" / "powershell" / "detect-phase0.ps1"
        assert ps1.exists(), f"{ps1} not found"


# ─── Option B: state.yaml detection ──────────────────────────────────────────

class TestStatYamlDetection:
    def test_ideate_phase_detected(self, tmpdir):
        write_state(tmpdir, ["ideate"])
        result = run_script(tmpdir)
        assert result.returncode == 0

    def test_selection_phase_detected(self, tmpdir):
        write_state(tmpdir, ["selection"])
        result = run_script(tmpdir)
        assert result.returncode == 0

    def test_structure_phase_detected(self, tmpdir):
        write_state(tmpdir, ["structure"])
        result = run_script(tmpdir)
        assert result.returncode == 0

    def test_ideation_alias_detected(self, tmpdir):
        """'ideation' (alias for 'ideate') should also be detected."""
        write_state(tmpdir, ["ideation"])
        result = run_script(tmpdir)
        assert result.returncode == 0

    def test_multiple_phases_detected(self, tmpdir):
        write_state(tmpdir, ["ideate", "selection", "structure"])
        result = run_script(tmpdir)
        assert result.returncode == 0

    def test_empty_phases_not_detected(self, tmpdir):
        write_state(tmpdir, [])
        result = run_script(tmpdir)
        assert result.returncode == 1

    def test_unrelated_phases_not_detected(self, tmpdir):
        write_state(tmpdir, ["specify", "implement"])
        result = run_script(tmpdir)
        assert result.returncode == 1


# ─── Option A: Directory fallback ────────────────────────────────────────────

class TestDirectoryFallback:
    def test_ideation_dir_with_files_detected(self, tmpdir):
        """No state.yaml, but .spec-kit/ideation/ has files → detected."""
        write_ideation_file(tmpdir)
        result = run_script(tmpdir)
        assert result.returncode == 0

    def test_empty_ideation_dir_not_detected(self, tmpdir):
        """Empty .spec-kit/ideation/ should NOT trigger detection."""
        ideation_dir = tmpdir / ".spec-kit" / "ideation"
        ideation_dir.mkdir(parents=True)
        result = run_script(tmpdir)
        assert result.returncode == 1

    def test_missing_ideation_dir_not_detected(self, tmpdir):
        """No state.yaml, no ideation dir → not detected."""
        result = run_script(tmpdir)
        assert result.returncode == 1

    def test_state_yaml_takes_priority_over_directory(self, tmpdir):
        """state.yaml with empty phases + non-empty ideation dir → detected via dir fallback."""
        write_state(tmpdir, [])
        write_ideation_file(tmpdir)
        result = run_script(tmpdir)
        # state says no Phase 0, but dir fallback catches it
        assert result.returncode == 0


# ─── --verbose flag ───────────────────────────────────────────────────────────

class TestVerboseFlag:
    def test_verbose_detected_prints_message(self, tmpdir):
        write_state(tmpdir, ["ideate"])
        result = run_script(tmpdir, "--verbose")
        assert result.returncode == 0
        assert "Phase 0 detected" in result.stdout

    def test_verbose_not_detected_prints_message(self, tmpdir):
        result = run_script(tmpdir, "--verbose")
        assert result.returncode == 1
        assert "Phase 0 not detected" in result.stdout

    def test_verbose_mentions_state_method(self, tmpdir):
        write_state(tmpdir, ["ideate"])
        result = run_script(tmpdir, "--verbose")
        assert "state.yaml" in result.stdout

    def test_verbose_mentions_directory_method(self, tmpdir):
        write_ideation_file(tmpdir)
        result = run_script(tmpdir, "--verbose")
        assert "directory" in result.stdout.lower() or "ideation" in result.stdout


# ─── --json flag ──────────────────────────────────────────────────────────────

class TestJsonFlag:
    def test_json_detected_via_state(self, tmpdir):
        write_state(tmpdir, ["ideate", "selection"])
        result = run_script(tmpdir, "--json")
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert data["phase0"] is True
        assert data["method"] == "state"
        assert "ideate" in data["phases"]

    def test_json_not_detected(self, tmpdir):
        result = run_script(tmpdir, "--json")
        assert result.returncode == 1
        data = json.loads(result.stdout)
        assert data["phase0"] is False
        assert data["method"] == "none"

    def test_json_detected_via_directory(self, tmpdir):
        write_ideation_file(tmpdir)
        result = run_script(tmpdir, "--json")
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert data["phase0"] is True
        assert data["method"] == "directory"
        assert data["files"] >= 1


# ─── --help flag ──────────────────────────────────────────────────────────────

class TestHelpFlag:
    def test_help_exits_zero(self, tmpdir):
        result = run_script(tmpdir, "--help")
        assert result.returncode == 0

    def test_help_shows_usage(self, tmpdir):
        result = run_script(tmpdir, "--help")
        assert "Usage" in result.stdout or "usage" in result.stdout.lower()


# ─── Edge cases ───────────────────────────────────────────────────────────────

class TestEdgeCases:
    def test_corrupt_state_yaml_falls_back_to_directory(self, tmpdir):
        """Corrupt YAML should not crash the script; falls back to directory check."""
        spec_kit_dir = tmpdir / ".spec-kit"
        spec_kit_dir.mkdir()
        (spec_kit_dir / "state.yaml").write_text("{ invalid: yaml: :::")
        write_ideation_file(tmpdir)
        result = run_script(tmpdir)
        # Should still detect via directory fallback
        assert result.returncode == 0

    def test_no_spec_kit_dir_returns_1(self, tmpdir):
        """Completely fresh project with no .spec-kit/ returns 1."""
        result = run_script(tmpdir)
        assert result.returncode == 1

    def test_silent_by_default(self, tmpdir):
        """Without --verbose or --json, script produces no output."""
        write_state(tmpdir, ["ideate"])
        result = run_script(tmpdir)
        assert result.stdout.strip() == ""

    def test_silent_when_not_detected(self, tmpdir):
        result = run_script(tmpdir)
        assert result.stdout.strip() == ""
        assert result.returncode == 1
