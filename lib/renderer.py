"""
Прямой JPEG-эндпоинт для iOS Shortcuts: GET /api/image -> новые обои 1170×2532.

Работает как serverless-функция Vercel. Цитаты лежат рядом в data/quotes.json,
фото берутся с GitHub Pages (и кешируются в памяти тёплого инстанса). Если фото
недоступны — рисуется процедурный фон, поэтому картинка отдаётся всегда.
"""

from __future__ import annotations

import io
import json
import math
import random
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

WIDTH = 1170
HEIGHT = 2532
JPEG_QUALITY = 90

ROOT = Path(__file__).resolve().parent.parent
QUOTES_FILE = ROOT / "data" / "quotes.json"
FONT_BOLD_FILE = ROOT / "fonts" / "PTSerif-Bold.ttf"
FONT_REGULAR_FILE = ROOT / "fonts" / "PTSerif-Regular.ttf"

PHOTO_MANIFEST = "https://misha1202.github.io/motivation-wallpaper/backgrounds/manifest.json"
PHOTO_BASE = "https://misha1202.github.io/motivation-wallpaper/backgrounds/"

FALLBACK_QUOTES = [
    {"text": "Ибо так возлюбил Бог мир, что отдал Сына Своего Единородного", "ref": "Иоанна 3:16"},
    {"text": "Уповай на Господа всем сердцем твоим", "ref": "Притчи 3:5"},
    {"text": "Господь — Пастырь мой; я ни в чём не буду нуждаться", "ref": "Псалом 22:1"},
    {"text": "Всё могу в укрепляющем меня Иисусе Христе", "ref": "Филиппийцам 4:13"},
]

TONES = [(28, 43, 74), (58, 42, 28), (15, 48, 52), (43, 32, 64), (59, 34, 38), (31, 51, 64)]

_quotes: list[dict] | None = None
_manifest: list[dict] | None = None
_photo_cache: dict[str, bytes] = {}


# ------------------------------------------------------------------ данные

def get_quotes() -> list[dict]:
    global _quotes
    if _quotes is None:
        try:
            with QUOTES_FILE.open(encoding="utf-8") as file:
                payload = json.load(file)
            valid = [
                quote
                for quote in payload.get("quotes", [])
                if isinstance(quote.get("text"), str) and 12 <= len(quote["text"]) <= 360
            ]
            _quotes = valid or FALLBACK_QUOTES
        except (OSError, ValueError, KeyError):
            _quotes = FALLBACK_QUOTES
    return _quotes


def get_manifest() -> list[dict]:
    global _manifest
    if _manifest is None:
        try:
            request = Request(PHOTO_MANIFEST, headers={"User-Agent": "motivation-wallpaper-api/1.0"})
            with urlopen(request, timeout=4) as response:
                payload = json.loads(response.read().decode("utf-8"))
            _manifest = [photo for photo in payload.get("photos", []) if photo.get("file")]
        except (HTTPError, URLError, TimeoutError, OSError, ValueError):
            _manifest = []
    return _manifest


def get_photo() -> Image.Image | None:
    photos = get_manifest()
    if not photos:
        return None

    for _ in range(3):
        photo = random.choice(photos)
        url = PHOTO_BASE + photo["file"]
        cached = _photo_cache.get(url)
        if cached:
            try:
                return Image.open(io.BytesIO(cached)).convert("RGB")
            except OSError:
                _photo_cache.pop(url, None)
        try:
            request = Request(url, headers={"User-Agent": "motivation-wallpaper-api/1.0"})
            with urlopen(request, timeout=6) as response:
                data = response.read()
            if len(data) < 20_000:
                continue
            if len(_photo_cache) >= 8:
                _photo_cache.clear()
            _photo_cache[url] = data
            return Image.open(io.BytesIO(data)).convert("RGB")
        except (HTTPError, URLError, TimeoutError, OSError):
            continue
    return None


# ------------------------------------------------------------------ фон

def _lerp(color_a: tuple[int, int, int], color_b: tuple[int, int, int], t: float) -> tuple[int, int, int]:
    return tuple(int(color_a[index] + (color_b[index] - color_a[index]) * t) for index in range(3))


def gradient(stops: list[tuple[float, tuple[int, int, int]]]) -> Image.Image:
    strip = Image.new("RGB", (1, HEIGHT))
    draw = ImageDraw.Draw(strip)
    for y in range(HEIGHT):
        position = y / (HEIGHT - 1)
        for index in range(len(stops) - 1):
            start_pos, start_color = stops[index]
            end_pos, end_color = stops[index + 1]
            if start_pos <= position <= end_pos:
                local = (position - start_pos) / max(end_pos - start_pos, 1e-6)
                draw.point((0, y), fill=_lerp(start_color, end_color, local))
                break
        else:
            draw.point((0, y), fill=stops[-1][1])
    return strip.resize((WIDTH, HEIGHT), Image.Resampling.BILINEAR)


def add_radial_glow(image: Image.Image, x: int, y: int, radius: int, color: tuple[int, int, int], strength: int = 90) -> Image.Image:
    layer = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    steps = 26
    for step in range(steps, 0, -1):
        current = int(radius * step / steps)
        alpha = int(strength * (1 - step / steps) ** 2)
        draw.ellipse([x - current, y - current, x + current, y + current], fill=color + (alpha,))
    layer = layer.filter(ImageFilter.GaussianBlur(radius * 0.12))
    return Image.alpha_composite(image.convert("RGBA"), layer)


def ridge_polygon(base_y: float, amplitude: float, phase: float) -> list[tuple[int, int]]:
    points = [(0, HEIGHT)]
    for x in range(0, WIDTH + 12, 12):
        wave = (
            math.sin(x / 260 + phase) * amplitude
            + math.sin(x / 97 + phase * 2.3) * amplitude * 0.35
            + math.sin(x / 41 + phase * 0.7) * amplitude * 0.12
        )
        points.append((x, int(base_y + wave)))
    points.append((WIDTH, HEIGHT))
    return points


def procedural_background() -> Image.Image:
    style = random.choice(["night", "night", "dusk", "ocean", "forest"])

    if style == "dusk":
        horizon = int(HEIGHT * 0.7)
        image = gradient(
            [
                (0.0, (5, 7, 16)),
                (0.32, (20, 26, 56)),
                (0.58, (75, 43, 77)),
                (0.8, (168, 90, 67)),
                (1.0, (233, 165, 98)),
            ]
        )
        sun_x = random.randint(int(WIDTH * 0.3), int(WIDTH * 0.7))
        sun_y = horizon - random.randint(40, 120)
        image = add_radial_glow(image, sun_x, sun_y, random.randint(380, 520), (255, 210, 150), 110)
        draw = ImageDraw.Draw(image)
        sun_r = random.randint(70, 110)
        draw.ellipse([sun_x - sun_r, sun_y - sun_r, sun_x + sun_r, sun_y + sun_r], fill=(255, 240, 210))
        for base, amplitude, color in [
            (horizon + 40, 55, (24, 26, 48)),
            (horizon + 130, 80, (15, 16, 32)),
            (horizon + 250, 110, (8, 9, 18)),
            (horizon + 430, 140, (4, 5, 10)),
        ]:
            draw.polygon(ridge_polygon(base, amplitude, random.uniform(0, math.tau)), fill=color)
        return image

    if style == "ocean":
        horizon = int(HEIGHT * 0.62)
        image = gradient(
            [
                (0.0, (6, 10, 22)),
                (0.4, (24, 39, 68)),
                (0.75, (76, 85, 110)),
                (1.0, (164, 120, 122)),
            ]
        )
        sun_x = random.randint(int(WIDTH * 0.3), int(WIDTH * 0.7))
        sun_y = horizon - random.randint(30, 90)
        image = add_radial_glow(image, sun_x, sun_y, random.randint(320, 460), (255, 215, 170), 100)
        draw = ImageDraw.Draw(image)
        sun_r = random.randint(58, 90)
        draw.ellipse([sun_x - sun_r, sun_y - sun_r, sun_x + sun_r, sun_y + sun_r], fill=(255, 244, 218))
        draw.rectangle([0, horizon, WIDTH, HEIGHT], fill=(9, 15, 27))
        reflection = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
        reflection_draw = ImageDraw.Draw(reflection)
        for index in range(70):
            position = index / 70
            y = horizon + int(position * (HEIGHT - horizon) * 0.9)
            spread = int(30 + position * 260)
            width = int(random.randint(18, 90) * (1 - position * 0.55))
            alpha = int(70 * (1 - position))
            x = sun_x + random.randint(-spread, spread)
            reflection_draw.ellipse([x - width, y - 3, x + width, y + 3], fill=(255, 215, 170, alpha))
        image = Image.alpha_composite(image.convert("RGBA"), reflection.filter(ImageFilter.GaussianBlur(1.2)))
        return image.convert("RGB")

    if style == "forest":
        image = gradient(
            [
                (0.0, (7, 20, 16)),
                (0.38, (13, 36, 29)),
                (0.7, (18, 49, 40)),
                (1.0, (5, 11, 9)),
            ]
        )
        light_x = random.randint(int(WIDTH * 0.25), int(WIDTH * 0.75))
        image = add_radial_glow(image, light_x, int(HEIGHT * 0.3), int(WIDTH * 0.9), (210, 235, 200), 70)
        draw = ImageDraw.Draw(image)
        for base, amplitude, color in [
            (HEIGHT * 0.72, 50, (14, 40, 32)),
            (HEIGHT * 0.8, 70, (9, 28, 23)),
            (HEIGHT * 0.89, 90, (5, 17, 14)),
            (HEIGHT * 0.97, 120, (2, 7, 5)),
        ]:
            draw.polygon(ridge_polygon(base, amplitude, random.uniform(0, math.tau)), fill=color)
        for _ in range(40):
            x = random.randint(-40, WIDTH + 40)
            base_y = int(HEIGHT * random.uniform(0.9, 1.02))
            height = random.randint(120, 420)
            width = int(height * random.uniform(0.22, 0.34))
            draw.polygon([(x, base_y - height), (x + width // 2, base_y), (x - width // 2, base_y)], fill=(2, 8, 6))
        return image

    # night
    image = gradient(
        [
            (0.0, (5, 7, 15)),
            (0.45, (11, 20, 40)),
            (0.72, (21, 34, 60)),
            (1.0, (6, 10, 20)),
        ]
    )
    stars = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    stars_draw = ImageDraw.Draw(stars)
    for _ in range(520):
        x = random.randint(0, WIDTH)
        y = random.randint(0, int(HEIGHT * 0.82))
        radius = random.uniform(0.6, 2.1)
        alpha = random.randint(45, 215)
        stars_draw.ellipse([x - radius, y - radius, x + radius, y + radius], fill=(255, 250, 235, alpha))
    image = Image.alpha_composite(image.convert("RGBA"), stars)
    moon_x = random.randint(int(WIDTH * 0.2), int(WIDTH * 0.8))
    moon_y = random.randint(int(HEIGHT * 0.12), int(HEIGHT * 0.3))
    moon_r = random.randint(46, 74)
    image = add_radial_glow(image, moon_x, moon_y, moon_r * 5, (255, 246, 220), 90)
    draw = ImageDraw.Draw(image)
    draw.ellipse([moon_x - moon_r, moon_y - moon_r, moon_x + moon_r, moon_y + moon_r], fill=(255, 249, 232))
    for base, amplitude, color in [
        (HEIGHT * 0.86, 46, (7, 11, 20)),
        (HEIGHT * 0.93, 70, (4, 7, 13)),
    ]:
        draw.polygon(ridge_polygon(base, amplitude, random.uniform(0, math.tau)), fill=color)
    return image.convert("RGB")


def photo_background() -> Image.Image | None:
    photo = get_photo()
    if photo is None:
        return None

    cover = max(WIDTH / photo.width, HEIGHT / photo.height)
    scale = cover * random.uniform(1.02, 1.18)
    width = int(photo.width * scale)
    height = int(photo.height * scale)
    photo = photo.resize((width, height), Image.Resampling.LANCZOS)
    x = int((width - WIDTH) * random.uniform(0.25, 0.75))
    y = int((height - HEIGHT) * random.uniform(0.2, 0.8))
    photo = photo.crop((x, y, x + WIDTH, y + HEIGHT))
    if random.random() < 0.5:
        photo = photo.transpose(Image.FLIP_LEFT_RIGHT)

    tone = Image.new("RGB", (WIDTH, HEIGHT), random.choice(TONES))
    photo = Image.blend(photo, ImageChops.soft_light(photo, tone), random.uniform(0.28, 0.45))
    photo = Image.blend(photo, Image.new("RGB", (WIDTH, HEIGHT), (5, 7, 13)), random.uniform(0.22, 0.4))
    return photo


# ------------------------------------------------------------------ текст и атмосфера

def _paste_mask(size: tuple[int, int], mask: Image.Image, top: int) -> Image.Image:
    canvas = Image.new("L", size, 0)
    canvas.paste(mask, (0, top))
    return canvas


def _apply_mask(image: Image.Image, mask: Image.Image, color: tuple[int, int, int] = (0, 0, 0)) -> Image.Image:
    layer = Image.new("RGBA", image.size, color + (255,))
    layer.putalpha(mask)
    return Image.alpha_composite(image.convert("RGBA"), layer)


def add_atmosphere(image: Image.Image) -> Image.Image:
    size = image.size

    radial = Image.radial_gradient("L").resize(size)
    vignette = radial.point(lambda value: int(min(255, (value / 255) ** 1.8 * 140)))
    image = _apply_mask(image, vignette)

    top_height = int(HEIGHT * 0.16)
    top_gradient = Image.linear_gradient("L").resize((WIDTH, top_height))
    top_mask = top_gradient.point(lambda value: int((1 - value / 255) * 95))
    image = _apply_mask(image, _paste_mask(size, top_mask, 0))

    bottom_height = int(HEIGHT * 0.58)
    bottom_gradient = Image.linear_gradient("L").resize((WIDTH, bottom_height))
    bottom_mask = bottom_gradient.point(lambda value: int((value / 255) * 140))
    image = _apply_mask(image, _paste_mask(size, bottom_mask, HEIGHT - bottom_height))

    shield_height = int(HEIGHT * 0.62)
    shield = Image.radial_gradient("L").point(lambda value: int(((255 - value) / 255) ** 1.7 * 115))
    shield = shield.resize((int(WIDTH * 1.1), shield_height))
    image = _apply_mask(image, _paste_mask(size, shield, int(HEIGHT * 0.605 - shield_height / 2)))

    return image


def capitalize_first(text: str) -> str:
    for index, char in enumerate(text):
        if char.isalpha():
            if char.islower():
                return text[:index] + char.upper() + text[index + 1 :]
            return text
    return text


def wrap_text(text: str, font: ImageFont.FreeTypeFont, max_width: int) -> list[str]:
    lines: list[str] = []
    for paragraph in text.split("\n"):
        line = ""
        for word in paragraph.split():
            candidate = f"{line} {word}".strip()
            if not line or font.getlength(candidate) <= max_width:
                line = candidate
                continue
            lines.append(line)
            if font.getlength(word) <= max_width:
                line = word
            else:
                chunk = ""
                for char in word:
                    if chunk and font.getlength(chunk + char) > max_width:
                        lines.append(chunk)
                        chunk = char
                    else:
                        chunk += char
                line = chunk
        if line:
            lines.append(line)
    return lines


def layout_quote(text: str, has_ref: bool) -> dict:
    max_width = WIDTH - 210
    max_block = HEIGHT * 0.5
    best = None

    for size in range(112, 52, -2):
        font = ImageFont.truetype(str(FONT_BOLD_FILE), size)
        lines = wrap_text(text, font, max_width)
        line_height = int(round(size * 1.27))
        ref_size = max(38, int(size * 0.4))
        gap = int(size * 0.6)
        block_height = len(lines) * line_height + (gap + ref_size if has_ref else 0)
        best = {
            "font": font,
            "size": size,
            "lines": lines,
            "line_height": line_height,
            "ref_size": ref_size,
            "gap": gap,
            "block_height": block_height,
        }
        if block_height <= max_block:
            break
    return best


def add_text(image: Image.Image, quote: dict) -> Image.Image:
    text = capitalize_first((quote.get("text") or "").strip())
    if not text:
        return image
    ref = (quote.get("ref") or "").strip()

    layout = layout_quote(text, bool(ref))
    start_y = int(HEIGHT * 0.605 - layout["block_height"] / 2)

    # Рисуем текст в вырезанном регионе, а не на всём холсте — экономит CPU/память.
    top = max(0, start_y - 150)
    bottom = min(HEIGHT, start_y + layout["block_height"] + 150)
    region_height = bottom - top
    region = image.crop((0, top, WIDTH, bottom)).convert("RGBA")

    decoration = Image.new("RGBA", (WIDTH, region_height), (0, 0, 0, 0))
    decoration_draw = ImageDraw.Draw(decoration)
    decoration_draw.rectangle(
        [WIDTH // 2 - 34, start_y - 58 - top, WIDTH // 2 + 34, start_y - 55 - top],
        fill=(231, 200, 145, 235),
    )

    ref_y = start_y + len(layout["lines"]) * layout["line_height"] + int(layout["gap"] * 0.45)

    shadow = Image.new("RGBA", (WIDTH, region_height), (0, 0, 0, 0))
    shadow_draw = ImageDraw.Draw(shadow)
    y = start_y
    for line in layout["lines"]:
        shadow_draw.text(
            (WIDTH // 2 + 5, y + 6 - top), line, font=layout["font"], fill=(0, 0, 0, 150), anchor="mt"
        )
        y += layout["line_height"]
    if ref:
        ref_font = ImageFont.truetype(str(FONT_REGULAR_FILE), layout["ref_size"])
        shadow_draw.text(
            (WIDTH // 2 + 3, ref_y + 3 - top),
            f"— {ref}",
            font=ref_font,
            fill=(0, 0, 0, 140),
            anchor="mt",
        )
    shadow = shadow.filter(ImageFilter.GaussianBlur(10))

    text_layer = Image.new("RGBA", (WIDTH, region_height), (0, 0, 0, 0))
    text_draw = ImageDraw.Draw(text_layer)
    y = start_y
    for line in layout["lines"]:
        text_draw.text(
            (WIDTH // 2, y - top), line, font=layout["font"], fill=(255, 253, 247, 247), anchor="mt"
        )
        y += layout["line_height"]
    if ref:
        ref_font = ImageFont.truetype(str(FONT_REGULAR_FILE), layout["ref_size"])
        text_draw.text(
            (WIDTH // 2, ref_y - top),
            f"— {ref}",
            font=ref_font,
            fill=(236, 226, 206, 205),
            anchor="mt",
        )

    combined = Image.alpha_composite(region, decoration)
    combined = Image.alpha_composite(combined, shadow)
    combined = Image.alpha_composite(combined, text_layer)
    image.paste(combined.convert("RGB"), (0, top))
    return image.convert("RGB")


def add_grain(image: Image.Image) -> Image.Image:
    image = image.convert("RGB")
    noise = Image.effect_noise((256, 256), 12).convert("RGB").resize((WIDTH, HEIGHT), Image.Resampling.BILINEAR)
    return Image.blend(image, noise, 0.02)


# ------------------------------------------------------------------ рендер

def render_wallpaper() -> bytes:
    quote = random.choice(get_quotes())
    background = photo_background() or procedural_background()
    image = add_atmosphere(background)
    image = add_text(image, quote)
    image = add_grain(image)

    buffer = io.BytesIO()
    image.save(buffer, format="JPEG", quality=JPEG_QUALITY, optimize=True, progressive=True)
    return buffer.getvalue()


def emergency_wallpaper() -> bytes:
    """Последний рубеж: градиент + текст стандартным шрифтом, без внешних файлов."""
    image = gradient([(0.0, (8, 10, 20)), (0.6, (24, 32, 56)), (1.0, (5, 7, 13))])
    draw = ImageDraw.Draw(image)
    font = ImageFont.load_default()
    quote = random.choice(FALLBACK_QUOTES)
    draw.multiline_text(
        (WIDTH // 2, int(HEIGHT * 0.55)),
        quote["text"],
        font=font,
        fill=(255, 253, 247),
        anchor="mm",
        align="center",
    )
    buffer = io.BytesIO()
    image.save(buffer, format="JPEG", quality=85)
    return buffer.getvalue()


class handler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:  # noqa: N802
        try:
            body = render_wallpaper()
        except Exception:  # noqa: BLE001
            import traceback

            traceback.print_exc()
            body = emergency_wallpaper()
        self.send_response(200)
        self.send_header("Content-Type", "image/jpeg")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store, no-cache, must-revalidate, max-age=0")
        self.send_header("Pragma", "no-cache")
        self.send_header("Content-Disposition", 'inline; filename="wallpaper.jpg"')
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def do_HEAD(self) -> None:  # noqa: N802
        self.send_response(200)
        self.send_header("Content-Type", "image/jpeg")
        self.send_header("Cache-Control", "no-store, no-cache, must-revalidate, max-age=0")
        self.end_headers()

    def log_message(self, *args) -> None:
        pass


if __name__ == "__main__":
    port = int(__import__("os").environ.get("PORT", "8766"))
    print(f"http://127.0.0.1:{port}/api/image")
    ThreadingHTTPServer(("0.0.0.0", port), handler).serve_forever()
