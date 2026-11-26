# Библейские обои — прямой JPEG API

Сервис для iOS Shortcuts: `GET /api/image` возвращает **новый JPEG 1170×2532**
при каждом запросе. Цитаты и шрифты лежат в репозитории, фото берутся
с GitHub Pages. Если фото недоступны — рисуется процедурный фон.

## Рабочий эндпоинт

```
https://motivation-wallpaper2.vercel.app/api/image
```

Превью: https://motivation-wallpaper2.vercel.app/

Проект Vercel развёрнут из копии `Misha1202/motivation-wallpaper_2`
(её создал Deploy Button). Изменения кода нужно пушить в эту копию —
Vercel пересоберёт проект автоматически.

## Шорткат на iPhone

1. В действии **«Получить содержимое URL»** укажи:
   `https://motivation-wallpaper2.vercel.app/api/image`
   (можно и корень `https://motivation-wallpaper2.vercel.app/` — он тоже
   отдаёт JPEG).
2. Следующее действие — **«Установить обои»** — не меняется.
   Важно: не используй «Получить текст из URL» или «Получить содержимое
   веб-страницы» — они вернут HTML.

Ответ отдаётся с `Cache-Control: no-store` и `Content-Type: image/jpeg`.
Если iOS всё равно закеширует, добавь в конец URL `?t=` и переменную
«Случайное число» (1–999999).

## Превью

HTML-страница с кнопкой «Новые обои»: https://motivation-wallpaper2.vercel.app/preview

## Локальный запуск

```bash
pip install -r requirements.txt
PORT=10000 python3 tools/serve.py     # http://127.0.0.1:10000/api/image
```

## Маршруты

| Путь | Ответ |
| --- | --- |
| `/`, `/api/image`, `/image`, `/wallpaper.jpg` | JPEG 1170×2532, без кеша |
| `/preview` | HTML-превью |
| `/health` | `ok` |

## Структура

- `api/index.py` — единая WSGI-функция Vercel, разбирает маршруты.
- `lib/renderer.py` — рендер: фото/процедурный фон, виньетка, текст с тенью,
  авто-подбор кегля, JPEG q90, аварийная картинка при ошибке.
- `tools/serve.py` — локальный HTTP-сервер.
- `data/quotes.json` — 5305 цитат.
- `fonts/` — PT Serif Bold/Regular (OFL).
- `vercel.json` — `includeFiles: "**/*"` (строкой, не массивом).
