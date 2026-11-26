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

1. В действии **«Получить содержимое»** укажи:
   `https://motivation-wallpaper2.vercel.app/api/image`
2. Следующее действие — **«Установить обои»** — не меняется.

Ответ отдаётся с `Cache-Control: no-store`. Если iOS всё равно закеширует,
добавь в конец URL `?t=` и переменную «Случайное число» (1–999999).

## Локальный запуск

```bash
pip install -r requirements.txt
PORT=10000 python3 tools/serve.py     # http://127.0.0.1:10000/api/image
```

## Маршруты

| Путь | Ответ |
| --- | --- |
| `/api/image`, `/image`, `/wallpaper.jpg` | JPEG 1170×2532, без кеша |
| `/health` | `ok` |
| `/` | HTML-превью |

## Структура

- `api/index.py` — единая WSGI-функция Vercel, разбирает маршруты.
- `lib/renderer.py` — рендер: фото/процедурный фон, виньетка, текст с тенью,
  авто-подбор кегля, JPEG q90, аварийная картинка при ошибке.
- `tools/serve.py` — локальный HTTP-сервер.
- `data/quotes.json` — 5305 цитат.
- `fonts/` — PT Serif Bold/Regular (OFL).
- `vercel.json` — `includeFiles: "**/*"` (строкой, не массивом).
