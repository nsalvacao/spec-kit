"""Tests for specify update command and passive update notification (issue #88)."""

import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from specify_cli import app, _fetch_latest_release, _get_update_cache_path, _load_update_cache, _save_update_cache, _check_for_update


runner = CliRunner()


# ---------------------------------------------------------------------------
# Helper fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def cache_dir(tmp_path):
    """Temporary directory for update cache."""
    return tmp_path / "specify-cli"


@pytest.fixture
def valid_cache(cache_dir):
    """Cache file created < 24h ago with a known version."""
    cache_dir.mkdir(parents=True)
    data = {
        "last_check": datetime.now(timezone.utc).isoformat(),
        "latest_version": "0.0.50",
        "release_url": "https://github.com/nsalvacao/spec-kit/releases/tag/v0.0.50",
    }
    cache_file = cache_dir / "update_cache.json"
    cache_file.write_text(json.dumps(data))
    return cache_file


@pytest.fixture
def stale_cache(cache_dir):
    """Cache file created > 24h ago."""
    cache_dir.mkdir(parents=True)
    old_time = datetime.fromtimestamp(time.time() - 90000, tz=timezone.utc).isoformat()
    data = {
        "last_check": old_time,
        "latest_version": "0.0.40",
        "release_url": "https://github.com/nsalvacao/spec-kit/releases/tag/v0.0.40",
    }
    cache_file = cache_dir / "update_cache.json"
    cache_file.write_text(json.dumps(data))
    return cache_file


# ---------------------------------------------------------------------------
# Cache helpers
# ---------------------------------------------------------------------------

class TestUpdateCachePath:
    def test_returns_path_object(self):
        path = _get_update_cache_path()
        assert isinstance(path, Path)
        assert path.name == "update_cache.json"

    def test_parent_named_specify_cli(self):
        path = _get_update_cache_path()
        assert path.parent.name == "specify-cli"


class TestLoadUpdateCache:
    def test_returns_none_when_file_missing(self, tmp_path):
        result = _load_update_cache(tmp_path / "nonexistent" / "update_cache.json")
        assert result is None

    def test_returns_none_when_corrupt_json(self, cache_dir):
        cache_dir.mkdir(parents=True)
        f = cache_dir / "update_cache.json"
        f.write_text("not json {{{")
        result = _load_update_cache(f)
        assert result is None

    def test_returns_none_when_stale(self, stale_cache):
        result = _load_update_cache(stale_cache)
        assert result is None

    def test_returns_data_when_fresh(self, valid_cache):
        result = _load_update_cache(valid_cache)
        assert result is not None
        assert result["latest_version"] == "0.0.50"

    def test_returns_none_when_missing_keys(self, cache_dir):
        cache_dir.mkdir(parents=True)
        f = cache_dir / "update_cache.json"
        f.write_text(json.dumps({"last_check": datetime.now(timezone.utc).isoformat()}))
        result = _load_update_cache(f)
        assert result is None


class TestSaveUpdateCache:
    def test_creates_parent_dirs(self, tmp_path):
        cache_file = tmp_path / "deep" / "nested" / "update_cache.json"
        _save_update_cache(cache_file, "0.0.99", "https://example.com/release")
        assert cache_file.exists()

    def test_written_data_is_valid_json(self, tmp_path):
        cache_file = tmp_path / "update_cache.json"
        _save_update_cache(cache_file, "1.2.3", "https://example.com")
        data = json.loads(cache_file.read_text())
        assert data["latest_version"] == "1.2.3"
        assert data["release_url"] == "https://example.com"
        assert "last_check" in data


# ---------------------------------------------------------------------------
# _fetch_latest_release
# ---------------------------------------------------------------------------

class TestFetchLatestRelease:
    def test_returns_version_and_url_on_success(self):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "tag_name": "v0.0.55",
            "html_url": "https://github.com/nsalvacao/spec-kit/releases/tag/v0.0.55",
        }
        with patch("specify_cli.client") as mock_client:
            mock_client.get.return_value = mock_response
            version, url = _fetch_latest_release()
        assert version == "0.0.55"
        assert "v0.0.55" in url

    def test_returns_none_on_network_error(self):
        import httpx
        with patch("specify_cli.client") as mock_client:
            mock_client.get.side_effect = httpx.RequestError("timeout")
            result = _fetch_latest_release()
        assert result is None

    def test_returns_none_on_non_200(self):
        mock_response = MagicMock()
        mock_response.status_code = 404
        with patch("specify_cli.client") as mock_client:
            mock_client.get.return_value = mock_response
            result = _fetch_latest_release()
        assert result is None

    def test_strips_v_prefix(self):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"tag_name": "v1.0.0", "html_url": "https://x.com"}
        with patch("specify_cli.client") as mock_client:
            mock_client.get.return_value = mock_response
            version, _ = _fetch_latest_release()
        assert version == "1.0.0"


# ---------------------------------------------------------------------------
# _check_for_update
# ---------------------------------------------------------------------------

class TestCheckForUpdate:
    def test_uses_cache_when_fresh(self, valid_cache):
        with patch("specify_cli._get_update_cache_path", return_value=valid_cache):
            with patch("specify_cli._fetch_latest_release") as mock_fetch:
                result = _check_for_update()
        # Should NOT call fetch when cache is fresh
        mock_fetch.assert_not_called()
        assert result is not None
        assert result["latest_version"] == "0.0.50"

    def test_fetches_when_cache_stale(self, stale_cache, tmp_path):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "tag_name": "v0.0.99",
            "html_url": "https://github.com/nsalvacao/spec-kit/releases/tag/v0.0.99",
        }
        new_cache = tmp_path / "specify-cli" / "update_cache.json"
        with patch("specify_cli._get_update_cache_path", return_value=new_cache):
            with patch("specify_cli.client") as mock_client:
                mock_client.get.return_value = mock_response
                result = _check_for_update()
        assert result is not None
        assert result["latest_version"] == "0.0.99"

    def test_returns_none_on_network_failure(self, tmp_path):
        import httpx
        cache_file = tmp_path / "specify-cli" / "update_cache.json"
        with patch("specify_cli._get_update_cache_path", return_value=cache_file):
            with patch("specify_cli.client") as mock_client:
                mock_client.get.side_effect = httpx.RequestError("timeout")
                result = _check_for_update()
        assert result is None

    def test_skips_when_ci_env(self, monkeypatch, valid_cache):
        monkeypatch.setenv("CI", "true")
        with patch("specify_cli._get_update_cache_path", return_value=valid_cache):
            result = _check_for_update(passive=True)
        assert result is None

    def test_skips_when_no_update_check_env(self, monkeypatch, valid_cache):
        monkeypatch.setenv("SPECIFY_NO_UPDATE_CHECK", "1")
        with patch("specify_cli._get_update_cache_path", return_value=valid_cache):
            result = _check_for_update(passive=True)
        assert result is None

    def test_does_not_skip_for_explicit_update_command(self, monkeypatch, valid_cache):
        """CI env should not skip explicit `specify update` call."""
        monkeypatch.setenv("CI", "true")
        with patch("specify_cli._get_update_cache_path", return_value=valid_cache):
            result = _check_for_update(passive=False)
        # passive=False means explicit call → do not skip
        assert result is not None


# ---------------------------------------------------------------------------
# specify update command
# ---------------------------------------------------------------------------

class TestUpdateCommand:
    def test_update_available_shows_versions(self):
        cache_data = {
            "latest_version": "0.0.99",
            "release_url": "https://github.com/nsalvacao/spec-kit/releases/tag/v0.0.99",
        }
        with patch("specify_cli._check_for_update", return_value=cache_data):
            with patch("specify_cli.get_speckit_version", return_value="0.0.29"):
                result = runner.invoke(app, ["update", "--no-upgrade"], catch_exceptions=False)
        assert "0.0.29" in result.output
        assert "0.0.99" in result.output

    def test_already_up_to_date(self):
        cache_data = {
            "latest_version": "0.0.29",
            "release_url": "https://github.com/nsalvacao/spec-kit/releases/tag/v0.0.29",
        }
        with patch("specify_cli._check_for_update", return_value=cache_data):
            with patch("specify_cli.get_speckit_version", return_value="0.0.29"):
                result = runner.invoke(app, ["update"], catch_exceptions=False)
        assert result.exit_code == 0
        assert "latest" in result.output.lower() or "up-to-date" in result.output.lower() or "✅" in result.output

    def test_check_flag_exits_1_when_update_available(self):
        cache_data = {
            "latest_version": "0.0.99",
            "release_url": "https://github.com/nsalvacao/spec-kit/releases/tag/v0.0.99",
        }
        with patch("specify_cli._check_for_update", return_value=cache_data):
            with patch("specify_cli.get_speckit_version", return_value="0.0.29"):
                result = runner.invoke(app, ["update", "--check"], catch_exceptions=False)
        assert result.exit_code == 1

    def test_check_flag_exits_0_when_up_to_date(self):
        cache_data = {
            "latest_version": "0.0.29",
            "release_url": "https://github.com/nsalvacao/spec-kit/releases/tag/v0.0.29",
        }
        with patch("specify_cli._check_for_update", return_value=cache_data):
            with patch("specify_cli.get_speckit_version", return_value="0.0.29"):
                result = runner.invoke(app, ["update", "--check"], catch_exceptions=False)
        assert result.exit_code == 0

    def test_shows_uv_upgrade_command(self):
        cache_data = {
            "latest_version": "0.0.99",
            "release_url": "https://github.com/nsalvacao/spec-kit/releases/tag/v0.0.99",
        }
        with patch("specify_cli._check_for_update", return_value=cache_data):
            with patch("specify_cli.get_speckit_version", return_value="0.0.29"):
                result = runner.invoke(app, ["update", "--no-upgrade"], catch_exceptions=False)
        assert "uv tool install" in result.output
        assert "nsalvacao/spec-kit" in result.output

    def test_network_failure_graceful(self):
        with patch("specify_cli._check_for_update", return_value=None):
            result = runner.invoke(app, ["update"], catch_exceptions=False)
        assert result.exit_code == 0
        # Should not crash, should show friendly message
        assert result.output.strip() != ""


# ---------------------------------------------------------------------------
# Passive notification in `specify check`
# ---------------------------------------------------------------------------

class TestPassiveNotification:
    def test_passive_notice_appears_in_check_when_update_available(self):
        cache_data = {
            "latest_version": "0.0.99",
            "release_url": "https://github.com/nsalvacao/spec-kit/releases/tag/v0.0.99",
        }
        with patch("specify_cli._check_for_update", return_value=cache_data):
            with patch("specify_cli.get_speckit_version", return_value="0.0.29"):
                with patch("specify_cli.check_tool", return_value=True):
                    result = runner.invoke(app, ["check"], catch_exceptions=False)
        assert "specify update" in result.output or "0.0.99" in result.output

    def test_no_passive_notice_when_up_to_date(self):
        cache_data = {
            "latest_version": "0.0.29",
            "release_url": "https://github.com/nsalvacao/spec-kit/releases/tag/v0.0.29",
        }
        with patch("specify_cli._check_for_update", return_value=cache_data):
            with patch("specify_cli.get_speckit_version", return_value="0.0.29"):
                with patch("specify_cli.check_tool", return_value=True):
                    result = runner.invoke(app, ["check"], catch_exceptions=False)
        # No update notice when already on latest
        assert "💡 Update available" not in result.output

    def test_no_passive_notice_when_network_fails(self):
        with patch("specify_cli._check_for_update", return_value=None):
            with patch("specify_cli.check_tool", return_value=True):
                result = runner.invoke(app, ["check"], catch_exceptions=False)
        assert "💡 Update available" not in result.output
