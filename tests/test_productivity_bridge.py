"""Tests for native productivity bridge server helpers."""

from __future__ import annotations

import json
from pathlib import Path
import threading
import time
from urllib.request import urlopen

from http.server import ThreadingHTTPServer

from specify_cli.productivity_bridge import HTML_PAGE, SERVICE_NAME, _status_payload, build_handler


def test_status_payload_reports_expected_artifacts(tmp_path: Path) -> None:
    (tmp_path / "TASKS.md").write_text("# tasks\n", encoding="utf-8")
    (tmp_path / "memory").mkdir()

    payload = _status_payload(project_root=tmp_path, host="127.0.0.1", port=8001, started_at=time.time() - 1)

    assert payload["service"] == SERVICE_NAME
    assert payload["artifacts"]["tasks"] is True
    assert payload["artifacts"]["memory"] is True
    assert payload["artifacts"]["claude"] is False
    assert payload["artifacts"]["cockpit_config"] is False


def test_bridge_status_endpoint_returns_service_metadata(tmp_path: Path) -> None:
    started_at = time.time()
    handler = build_handler(tmp_path, "127.0.0.1", 0, started_at)
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    host, port = server.server_address

    try:
        with urlopen(f"http://{host}:{port}/api/status", timeout=2.0) as response:
            payload = json.loads(response.read().decode("utf-8"))
        assert payload["service"] == SERVICE_NAME
        assert payload["project_root"] == str(tmp_path)
        assert response.headers.get("X-Content-Type-Options") == "nosniff"
        assert response.headers.get("X-Frame-Options") == "DENY"
        assert response.headers.get("Referrer-Policy") == "no-referrer"
        assert response.headers.get("Cross-Origin-Resource-Policy") == "same-origin"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2.0)


def test_bridge_dashboard_uses_text_nodes_for_status_values() -> None:
    assert "textContent = String(value ?? '')" in HTML_PAGE
    assert "entries.map" not in HTML_PAGE


def test_bridge_root_includes_csp_header(tmp_path: Path) -> None:
    started_at = time.time()
    handler = build_handler(tmp_path, "127.0.0.1", 0, started_at)
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    host, port = server.server_address

    try:
        with urlopen(f"http://{host}:{port}/", timeout=2.0) as response:
            response.read()
        assert response.headers.get("Content-Security-Policy")
        assert response.headers.get("X-Frame-Options") == "DENY"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2.0)
