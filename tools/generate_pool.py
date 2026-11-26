"""Генератор пула обоев для GitHub Pages (без сервера)."""

from __future__ import annotations

import json
import random
import sys
from pathlib import Path
from urllib.request import Request, urlopen

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import lib.renderer as image  # noqa: E402

CACHE = ROOT / "cache" / "photos"
CACHE.mkdir(parents=True, exist_ok=True)


def download_photos() -> list[Image.Image]:
    request = Request(image.PHOTO_MANIFEST, headers={"User-Agent": "motivation-wallpaper-pool/1.0"})
    with urlopen(request, timeout=20) as response:
        manifest = json.loads(response.read().decode("utf-8"))

    photos: list[Image.Image] = []
    for photo in manifest.get("photos", []):
        name = photo.get("file")
        if not name:
            continue
        path = CACHE / name
        if not path.exists():
            try:
                req = Request(image.PHOTO_BASE + name, headers={"User-Agent": "motivation-wallpaper-pool/1.0"})
                with urlopen(req, timeout=20) as response:
                    path.write_bytes(response.read())
            except Exception as error:  # noqa: BLE001
                print("skip", name, error)
                continue
        opened = Image.open(path).convert("RGB")
        opened.thumbnail((1500, 3300), Image.Resampling.LANCZOS)
        photos.append(opened)
    return photos


def main() -> None:
    count = int(sys.argv[1]) if len(sys.argv) > 1 else 10
    out_dir = Path(sys.argv[2]) if len(sys.argv) > 2 else ROOT / "pool"
    out_dir.mkdir(parents=True, exist_ok=True)

    photos = download_photos()
    print("photos:", len(photos))
    if not photos:
        raise SystemExit("no photos")

    def local_photo() -> Image.Image:
        return random.choice(photos).copy()

    image.get_photo = local_photo  # type: ignore[assignment]
    quotes = image.get_quotes()
    random.shuffle(quotes)
    total_bytes = 0

    for index in range(1, count + 1):
        quote = quotes[(index - 1) % len(quotes)]
        background = image.photo_background() or image.procedural_background()
        canvas = image.add_atmosphere(background)
        canvas = image.add_text(canvas, quote)
        canvas = image.add_grain(canvas)
        buffer = __import__("io").BytesIO()
        canvas.save(buffer, format="JPEG", quality=85, optimize=True, progressive=True)
        data = buffer.getvalue()
        total_bytes += len(data)
        (out_dir / f"{index}.jpg").write_bytes(data)
        if index % 25 == 0:
            print(index, f"avg={total_bytes / index / 1024:.0f}KB", flush=True)

    print("done", count, f"total={total_bytes / 1024 / 1024:.0f}MB")


if __name__ == "__main__":
    main()
