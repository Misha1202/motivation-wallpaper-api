"""HTTP-сервер для Render: /api/image (JPEG), /health, / (превью)."""

from __future__ import annotations

import os
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from api.index import HTML  # noqa: E402
from lib.renderer import emergency_wallpaper, render_wallpaper  # noqa: E402


class App(BaseHTTPRequestHandler):
    def do_GET(self) -> None:  # noqa: N802
        path = urlparse(self.path).path.rstrip("/") or "/"

        if path in ("/", "/index.html"):
            self._send(HTML.encode("utf-8"), "text/html; charset=utf-8")
        elif path in ("/health", "/healthz"):
            self._send(b"ok", "text/plain; charset=utf-8")
        elif path in ("/api/image", "/image", "/wallpaper.jpg"):
            try:
                body = render_wallpaper()
            except Exception:  # noqa: BLE001
                import traceback

                traceback.print_exc()
                body = emergency_wallpaper()
            self._send(
                body,
                "image/jpeg",
                extra={
                    "Content-Disposition": 'inline; filename="wallpaper.jpg"',
                    "Access-Control-Allow-Origin": "*",
                },
            )
        else:
            self._send(b"Not found", "text/plain; charset=utf-8", status=404)

    def do_HEAD(self) -> None:  # noqa: N802
        path = urlparse(self.path).path.rstrip("/") or "/"
        if path in ("/api/image", "/image", "/wallpaper.jpg", "/health", "/"):
            self.send_response(200)
            self.send_header("Content-Type", "image/jpeg" if "image" in path or "wallpaper" in path else "text/plain")
            self.send_header("Cache-Control", "no-store, no-cache, must-revalidate, max-age=0")
            self.end_headers()
        else:
            self.send_response(404)
            self.end_headers()

    def _send(self, body: bytes, content_type: str, status: int = 200, extra: dict | None = None) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store, no-cache, must-revalidate, max-age=0")
        self.send_header("Pragma", "no-cache")
        for key, value in (extra or {}).items():
            self.send_header(key, value)
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(body)

    def log_message(self, *args) -> None:
        pass


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "10000"))
    print(f"listening on 0.0.0.0:{port}")
    ThreadingHTTPServer(("0.0.0.0", port), App).serve_forever()
