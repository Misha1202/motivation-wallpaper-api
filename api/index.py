from __future__ import annotations

from http.server import BaseHTTPRequestHandler

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


class handler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:  # noqa: N802
        body = HTML.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args) -> None:
        pass
