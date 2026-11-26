# Библейские обои — прямой JPEG API

Мини-сервис для iOS Shortcuts: `GET /api/image` возвращает **новый JPEG 1170×2532**
при каждом запросе. Цитаты и шрифты лежат в репозитории, фото подтягиваются
с GitHub Pages и кешируются в памяти. Если фото недоступны — рисуется
процедурный фон, поэтому картинка отдаётся всегда.

Сайт: https://misha1202.github.io/motivation-wallpaper/

## Деплой

[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https%3A%2F%2Fgithub.com%2FMisha1202%2Fmotivation-wallpaper-api&project-name=motivation-wallpaper-api&repository-name=motivation-wallpaper-api)

После деплоя адрес картинки:

```
https://<проект>.vercel.app/api/image
```

Проверить в браузере: открыть этот URL — должна открыться картинка,
обновление страницы даёт новую.

## Настройка шортката на iPhone

1. Открой «Команды» → свой шорткат «сменить обои».
2. В действии **«Получить содержимое»** замени URL на `https://<проект>.vercel.app/api/image`.
3. Остальные действия не меняются: «Установить обои» берёт картинку из результата.

Если iOS закеширует ответ, добавь в URL параметр с текущим временем:
`.../api/image?t=` + переменная «Текущая дата» (формат Unix). Но у функции
стоит `Cache-Control: no-store`, обычно кеш не мешает.

## Локальный запуск

```bash
pip install -r requirements.txt
python3 api/image.py        # http://127.0.0.1:8766/api/image
```

## Как это устроено

- `api/image.py` — рендер: фото/процедурный фон, виньетка, текст с тенью,
  авто-подбор кегля, JPEG q90.
- `data/quotes.json` — 5305 цитат (собраны из azbyka.ru).
- `fonts/` — PT Serif Bold/Regular (OFL).
- `api/index.py` — страница-превью.
