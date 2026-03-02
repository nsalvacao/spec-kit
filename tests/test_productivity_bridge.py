"""Tests for native productivity bridge server helpers."""

from __future__ import annotations

import json
from pathlib import Path
import threading
import time
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from http.server import ThreadingHTTPServer

from specify_cli.productivity_bridge import HTML_PAGE, SERVICE_NAME, _status_payload, build_handler


def _http_get_json(url: str) -> tuple[int, dict[str, object], object]:
    with urlopen(url, timeout=2.0) as response:
        payload = json.loads(response.read().decode("utf-8"))
        return response.status, payload, response


def _http_post_json(url: str, payload: dict[str, object]) -> tuple[int, dict[str, object]]:
    request = Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urlopen(request, timeout=2.0) as response:
        return response.status, json.loads(response.read().decode("utf-8"))


def test_status_payload_reports_expected_artifacts(tmp_path: Path) -> None:
    (tmp_path / "TASKS.md").write_text("# tasks\n", encoding="utf-8")
    (tmp_path / "memory").mkdir()

    payload = _status_payload(project_root=tmp_path, host="127.0.0.1", port=8001, started_at=time.time() - 1)

    assert payload["service"] == SERVICE_NAME
    assert payload["artifacts"]["tasks"] is True
    assert payload["artifacts"]["memory"] is True
    assert payload["artifacts"]["claude"] is False
    assert payload["artifacts"]["cockpit_config"] is False
    assert payload["paths"]["tasks"] == "TASKS.md"
    assert payload["paths"]["memory"] == "memory"


def test_bridge_status_endpoint_returns_service_metadata(tmp_path: Path) -> None:
    started_at = time.time()
    handler = build_handler(tmp_path, "127.0.0.1", 0, started_at)
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    host, port = server.server_address

    try:
        status, payload, response = _http_get_json(f"http://{host}:{port}/api/status")
        assert status == 200
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
    assert "textContent = safeText(value)" in HTML_PAGE
    assert "innerHTML" not in HTML_PAGE


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


def test_tasks_endpoint_roundtrip(tmp_path: Path) -> None:
    started_at = time.time()
    handler = build_handler(tmp_path, "127.0.0.1", 0, started_at)
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    host, port = server.server_address

    try:
        status, payload, _ = _http_get_json(f"http://{host}:{port}/api/tasks")
        assert status == 200
        assert payload["summary"]["total"] == 0

        status, payload = _http_post_json(
            f"http://{host}:{port}/api/tasks",
            {
                "sections": {
                    "Active": [{"body": "Ship A3", "checked": False}],
                    "Waiting On": [],
                    "Someday": [],
                    "Done": [{"body": "A2 delivered", "checked": True}],
                }
            },
        )
        assert status == 200
        assert payload["ok"] is True

        status, payload, _ = _http_get_json(f"http://{host}:{port}/api/tasks")
        assert status == 200
        assert payload["summary"]["total"] == 2
        assert payload["summary"]["checked"] == 1
        assert (tmp_path / "TASKS.md").exists()
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2.0)


def test_memory_endpoint_rejects_path_traversal(tmp_path: Path) -> None:
    started_at = time.time()
    handler = build_handler(tmp_path, "127.0.0.1", 0, started_at)
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    host, port = server.server_address

    try:
        request = Request(
            f"http://{host}:{port}/api/memory",
            data=json.dumps({"path": "../secrets.txt", "content": "x"}).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            urlopen(request, timeout=2.0)
        except HTTPError as exc:
            payload = json.loads(exc.read().decode("utf-8"))
            assert exc.code == 400
            assert payload["code"] == "invalid_path"
        else:
            raise AssertionError("Expected HTTPError for traversal path.")
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2.0)


def test_memory_endpoint_roundtrip(tmp_path: Path) -> None:
    started_at = time.time()
    handler = build_handler(tmp_path, "127.0.0.1", 0, started_at)
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    host, port = server.server_address

    try:
        status, payload = _http_post_json(
            f"http://{host}:{port}/api/memory",
            {"path": "memory/notes.md", "content": "# notes\nhello\n"},
        )
        assert status == 200
        assert payload["ok"] is True

        status, payload, _ = _http_get_json(f"http://{host}:{port}/api/memory")
        assert status == 200
        assert payload["files"]
        assert payload["files"][0]["path"] == "memory/notes.md"

        status, payload, _ = _http_get_json(f"http://{host}:{port}/api/memory?path=memory/notes.md")
        assert status == 200
        assert "hello" in payload["content"]
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2.0)


def test_pulse_and_drift_endpoints(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text("ok\n", encoding="utf-8")
    (tmp_path / "TASKS.md").write_text("# Tasks\n\n## Active\n- [ ] A\n", encoding="utf-8")

    started_at = time.time()
    handler = build_handler(tmp_path, "127.0.0.1", 0, started_at)
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    host, port = server.server_address

    try:
        status, pulse, _ = _http_get_json(f"http://{host}:{port}/api/pulse")
        assert status == 200
        assert pulse["task_counts"]["total"] == 1
        assert pulse["essential_files"]

        status, drift1, _ = _http_get_json(f"http://{host}:{port}/api/drift")
        assert status == 200
        assert isinstance(drift1["cursor"], int)

        _http_post_json(
            f"http://{host}:{port}/api/memory",
            {"path": "memory/new.md", "content": "drift\n"},
        )
        status, drift2, _ = _http_get_json(f"http://{host}:{port}/api/drift")
        assert status == 200
        assert any("memory/new.md" in path for path in drift2["changed"])
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2.0)


def test_exec_endpoint_rejects_non_whitelisted_cli(tmp_path: Path) -> None:
    started_at = time.time()
    handler = build_handler(tmp_path, "127.0.0.1", 0, started_at)
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    host, port = server.server_address

    try:
        request = Request(
            f"http://{host}:{port}/api/exec",
            data=json.dumps({"prompt": "hi", "mode": "cli", "cli": "bash"}).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            urlopen(request, timeout=2.0)
        except HTTPError as exc:
            payload = json.loads(exc.read().decode("utf-8"))
            assert exc.code == 400
            assert payload["code"] == "invalid_exec_request"
        else:
            raise AssertionError("Expected HTTPError for non-whitelisted CLI.")
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2.0)
