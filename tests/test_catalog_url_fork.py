"""
Tests for issue #80: DEFAULT_CATALOG_URL and catalog.json must point to the fork
(nsalvacao/spec-kit), not the upstream (github/spec-kit).

RED phase — these tests fail until the fix is applied.
"""

import json
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).parent.parent
CATALOG_JSON = REPO_ROOT / "extensions" / "catalog.json"
FORK_RAW_BASE = "https://raw.githubusercontent.com/nsalvacao/spec-kit/main"
UPSTREAM_RAW_BASE = "https://raw.githubusercontent.com/github/spec-kit/main"
EXPECTED_CATALOG_URL = f"{FORK_RAW_BASE}/extensions/catalog.json"


# ---------------------------------------------------------------------------
# extensions.py DEFAULT_CATALOG_URL
# ---------------------------------------------------------------------------


def test_default_catalog_url_points_to_fork():
    """ExtensionCatalog.DEFAULT_CATALOG_URL must reference the fork, not upstream."""
    from specify_cli.extensions import ExtensionCatalog

    assert ExtensionCatalog.DEFAULT_CATALOG_URL == EXPECTED_CATALOG_URL, (
        f"DEFAULT_CATALOG_URL must point to the fork nsalvacao/spec-kit.\n"
        f"  Expected: {EXPECTED_CATALOG_URL}\n"
        f"  Got:      {ExtensionCatalog.DEFAULT_CATALOG_URL}"
    )


def test_default_catalog_url_not_upstream():
    """DEFAULT_CATALOG_URL must NOT reference the upstream github/spec-kit."""
    from specify_cli.extensions import ExtensionCatalog

    assert UPSTREAM_RAW_BASE not in ExtensionCatalog.DEFAULT_CATALOG_URL, (
        "DEFAULT_CATALOG_URL still points to upstream github/spec-kit. "
        "Update extensions.py to use nsalvacao/spec-kit."
    )


# ---------------------------------------------------------------------------
# extensions/catalog.json catalog_url field
# ---------------------------------------------------------------------------


def test_catalog_json_exists():
    """extensions/catalog.json must exist."""
    assert CATALOG_JSON.exists(), "extensions/catalog.json not found"


def test_catalog_json_catalog_url_points_to_fork():
    """catalog_url field in extensions/catalog.json must reference the fork."""
    data = json.loads(CATALOG_JSON.read_text(encoding="utf-8"))
    catalog_url = data.get("catalog_url", "")
    assert catalog_url == EXPECTED_CATALOG_URL, (
        f"extensions/catalog.json 'catalog_url' must point to the fork.\n"
        f"  Expected: {EXPECTED_CATALOG_URL}\n"
        f"  Got:      {catalog_url}"
    )


def test_catalog_json_catalog_url_not_upstream():
    """catalog_url in catalog.json must NOT reference upstream github/spec-kit."""
    data = json.loads(CATALOG_JSON.read_text(encoding="utf-8"))
    catalog_url = data.get("catalog_url", "")
    assert UPSTREAM_RAW_BASE not in catalog_url, (
        "extensions/catalog.json 'catalog_url' still points to upstream github/spec-kit."
    )
