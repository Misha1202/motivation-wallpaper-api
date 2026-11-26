"""Единая Vercel-функция (WSGI): /api/image -> JPEG, / -> превью.

Vercel направляет все пути в этот файл, поэтому маршруты разбираем сами.
Раньше здесь был BaseHTTPRequestHandler, который отвечал HTML на любой путь —
из-за этого /api/image возвращал страницу вместо картинки.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from lib.renderer import emergency_wallpaper, render_wallpaper  # noqa: E402

HTML = """<!doctype html>
<html lang="ru">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Библейские обои — API</title>
<style>
  :root { color-scheme: dark; }
  body { margin: 0; min-height: 100vh; display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 18px; background: #07070b; color: #f4efe5; font-family: Georgia, serif; padding: 20px; }
  img { width: min(390px, 92vw); border-radius: 20px; box-shadow: 0 30px 80px rgba(0,0,0,.6); display: block; }
  button { appearance: none; border: 0; border-radius: 14px; padding: 14px 22px; font: 600 15px Georgia, serif; background: linear-gradient(135deg, #f0d6a8, #d9b578); color: #1b1409; cursor: pointer; }
  p { margin: 0; font-size: 13px; color: rgba(244,239,229,.55); text-align: center; line-height: 1.5; }
  a { color: #e7c891; }
</style>
</head>
<body>
  <img id="wallpaper" src="/api/image" alt="Библейские обои">
  <button id="refresh" type="button">Новые обои</button>
  <p>Прямой JPEG: <a href="/api/image">/api/image</a><br>Сайт: <a href="https://misha1202.github.io/motivation-wallpaper/">misha1202.github.io/motivation-wallpaper</a></p>
  <script>
    document.getElementById('refresh').addEventListener('click', () => {
      document.getElementById('wallpaper').src = '/api/image?t=' + Date.now();
    });
  </script>
</body>
</html>
"""

IMAGE_PATHS = {"/", "/api", "/api/image", "/image", "/wallpaper.jpg"}
NO_CACHE = [
    ("Cache-Control", "no-store, no-cache, must-revalidate, max-age=0"),
    ("Pragma", "no-cache"),
]


def _respond(start_response, status: str, body: bytes, content_type: str, extra: list | None = None):
    headers = [("Content-Type", content_type), ("Content-Length", str(len(body)))]
    headers += NO_CACHE
    headers += extra or []
    start_response(status, headers)
    return [body]


def app(environ, start_response):
    path = (environ.get("PATH_INFO") or "/").rstrip("/") or "/"
    method = (environ.get("REQUEST_METHOD") or "GET").upper()

    if method not in ("GET", "HEAD"):
        return _respond(start_response, "405 Method Not Allowed", b"Method not allowed", "text/plain; charset=utf-8")

    if path in IMAGE_PATHS:
        try:
            body = render_wallpaper()
        except Exception:  # noqa: BLE001
            import traceback

            traceback.print_exc()
            body = emergency_wallpaper()
        extra = [
            ("Content-Disposition", 'inline; filename="wallpaper.jpg"'),
            ("Access-Control-Allow-Origin", "*"),
        ]
        return _respond(start_response, "200 OK", body if method == "GET" else b"", "image/jpeg", extra)

    if path in ("/preview", "/index.html"):
        body = HTML.encode("utf-8")
        return _respond(start_response, "200 OK", body if method == "GET" else b"", "text/html; charset=utf-8")

    if path in ("/health", "/healthz"):
        return _respond(start_response, "200 OK", b"ok", "text/plain; charset=utf-8")

    return _respond(start_response, "404 Not Found", b"Not found", "text/plain; charset=utf-8")
