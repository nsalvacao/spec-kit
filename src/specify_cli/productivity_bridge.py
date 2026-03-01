"""Minimal native cockpit bridge server for productivity start flow."""

from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path
import sys
import time
from typing import Any
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse


SERVICE_NAME = "specify-productivity-cockpit"
LOGGER = logging.getLogger("specify_cli.productivity_bridge")

HTML_PAGE = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Spec Kit Productivity Cockpit</title>
  <style>
    body { font-family: ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Arial, sans-serif; margin: 0; background: #f7f6f3; color: #1e1e1e; }
    .wrap { max-width: 860px; margin: 48px auto; padding: 0 20px; }
    .card { background: #fff; border: 1px solid #e5e4df; border-radius: 14px; padding: 24px; box-shadow: 0 8px 30px rgba(0,0,0,0.06); }
    h1 { margin: 0 0 8px; font-size: 1.5rem; }
    p { color: #555; }
    code { background: #f1efe9; padding: 2px 6px; border-radius: 6px; }
    .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 12px; margin-top: 16px; }
    .k { background: #faf9f5; border: 1px solid #eceae3; border-radius: 10px; padding: 12px; }
    .k .l { font-size: 0.78rem; color: #666; text-transform: uppercase; letter-spacing: 0.04em; }
    .k .v { margin-top: 6px; font-weight: 600; word-break: break-word; }
    .hint { margin-top: 16px; font-size: 0.95rem; }
  </style>
</head>
<body>
  <div class="wrap">
    <div class="card">
      <h1>Productivity Cockpit (Native)</h1>
      <p>A1 start flow is active. Full parity UI/features continue in follow-up issues.</p>
      <div class="grid" id="statusGrid"></div>
      <div class="hint">
        API status endpoint: <code>/api/status</code>
      </div>
    </div>
  </div>
  <script>
    async function load() {
      try {
        const r = await fetch('/api/status');
        const data = await r.json();
        const entries = [
          ['Service', data.service],
          ['Host', data.host],
          ['Port', String(data.port)],
          ['Project Root', data.project_root],
          ['Tasks', data.artifacts?.tasks ? 'present' : 'missing'],
          ['CLAUDE', data.artifacts?.claude ? 'present' : 'missing'],
          ['Memory Dir', data.artifacts?.memory ? 'present' : 'missing'],
          ['Config', data.artifacts?.cockpit_config ? 'present' : 'missing']
        ];
        const grid = document.getElementById('statusGrid');
        grid.replaceChildren();
        for (const [label, value] of entries) {
          const card = document.createElement('div');
          card.className = 'k';
          const labelNode = document.createElement('div');
          labelNode.className = 'l';
          labelNode.textContent = label;
          const valueNode = document.createElement('div');
          valueNode.className = 'v';
          valueNode.textContent = String(value ?? '');
          card.append(labelNode, valueNode);
          grid.appendChild(card);
        }
      } catch (err) {
        const grid = document.getElementById('statusGrid');
        grid.replaceChildren();
        const card = document.createElement('div');
        card.className = 'k';
        const labelNode = document.createElement('div');
        labelNode.className = 'l';
        labelNode.textContent = 'Error';
        const valueNode = document.createElement('div');
        valueNode.className = 'v';
        valueNode.textContent = String(err);
        card.append(labelNode, valueNode);
        grid.appendChild(card);
      }
    }
    load();
  </script>
</body>
</html>
"""


def _status_payload(*, project_root: Path, host: str, port: int, started_at: float) -> dict[str, Any]:
    return {
        "service": SERVICE_NAME,
        "host": host,
        "port": port,
        "project_root": str(project_root),
        "started_at_epoch": started_at,
        "uptime_seconds": round(time.time() - started_at, 3),
        "artifacts": {
            "tasks": (project_root / "TASKS.md").exists(),
            "claude": (project_root / "CLAUDE.md").exists(),
            "memory": (project_root / "memory").exists(),
            "cockpit_config": (project_root / ".cockpit.json").exists(),
        },
    }


def build_handler(project_root: Path, host: str, port: int, started_at: float) -> type[BaseHTTPRequestHandler]:
    class Handler(BaseHTTPRequestHandler):
        def _send_common_security_headers(self) -> None:
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("X-Frame-Options", "DENY")
            self.send_header("Referrer-Policy", "no-referrer")
            self.send_header("Cross-Origin-Resource-Policy", "same-origin")

        def _send_json(self, payload: dict[str, Any], status: int = 200) -> None:
            body = json.dumps(payload).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self._send_common_security_headers()
            self.end_headers()
            self.wfile.write(body)

        def _send_html(self, html: str, status: int = 200) -> None:
            body = html.encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self._send_common_security_headers()
            self.send_header(
                "Content-Security-Policy",
                (
                    "default-src 'self'; "
                    "script-src 'self' 'unsafe-inline'; "
                    "style-src 'self' 'unsafe-inline'; "
                    "img-src 'self' data:; "
                    "object-src 'none'; "
                    "base-uri 'none'; "
                    "frame-ancestors 'none'; "
                    "connect-src 'self'"
                ),
            )
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self) -> None:  # noqa: N802
            parsed = urlparse(self.path)
            if parsed.path == "/api/status":
                self._send_json(
                    _status_payload(project_root=project_root, host=host, port=port, started_at=started_at)
                )
                return
            if parsed.path in {"/", "/index.html"}:
                self._send_html(HTML_PAGE)
                return
            self._send_json({"error": "not found", "code": "not_found"}, status=404)

        def log_message(self, format: str, *args: Any) -> None:  # noqa: A003
            # Keep logs concise in detached mode.
            LOGGER.info(format, *args)

    return Handler


def _validate_project_root(project_root: Path) -> Path:
    root = project_root.resolve()
    if not root.exists() or not root.is_dir():
        raise ValueError(f"Invalid project root: {root}")

    cwd = Path.cwd().resolve()
    if root != cwd:
        try:
            root.relative_to(cwd)
        except ValueError as exc:
            raise ValueError(
                f"Invalid project root: {root}. Root must be current working directory or a child path."
            ) from exc
    return root


def run_server(project_root: Path, host: str, port: int) -> int:
    try:
        root = _validate_project_root(project_root)
    except ValueError as exc:
        print(str(exc), flush=True)
        return 2

    started_at = time.time()
    handler = build_handler(root, host, port, started_at)
    server = ThreadingHTTPServer((host, port), handler)
    server.daemon_threads = True
    LOGGER.info("%s listening on http://%s:%s", SERVICE_NAME, host, port)
    LOGGER.info("project_root=%s", root)

    try:
        server.serve_forever(poll_interval=0.2)
    except KeyboardInterrupt:
        pass
    except Exception:
        LOGGER.exception("Bridge server stopped due to unexpected error")
        return 1
    finally:
        server.server_close()
    return 0


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run native productivity cockpit bridge.")
    parser.add_argument("--project-root", required=True, help="Project root path.")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind.")
    parser.add_argument("--port", default=8001, type=int, help="Port to bind.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    if not logging.getLogger().handlers:
        logging.basicConfig(level=logging.INFO, format="[bridge] %(message)s")
    args = _parse_args(argv)
    return run_server(Path(args.project_root), args.host, int(args.port))


if __name__ == "__main__":
    sys.exit(main())
