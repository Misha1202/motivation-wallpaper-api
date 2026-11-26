# Библейские обои — прямой JPEG API

Мини-сервис для iOS Shortcuts: `GET /api/image` возвращает **новый JPEG 1170×2532**
при каждом запросе. Цитаты и шрифты лежат в репозитории, фото подтягиваются
с GitHub Pages и кешируются в памяти. Если фото недоступны — рисуется
процедурный фон, поэтому картинка отдаётся всегда.

Сайт: https://misha1202.github.io/motivation-wallpaper/

## Деплой на Render (основной вариант)

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/Misha1202/motivation-wallpaper-api)

1. Нажми кнопку → войди через GitHub → **Apply**.
2. Render создаст сервис `bible-wallpaper-image` по `render.yaml`
   (free, Frankfurt, health check `/health`).
3. Адрес картинки:

   ```
   https://<service>.onrender.com/api/image
   ```

4. Чтобы free-инстанс не засыпал (сон через ~15 минут, холодный старт
   30–60 секунд), заведи бесплатный монитор на
   `https://<service>.onrender.com/health` каждые 5 минут:
   UptimeRobot, cron-job.org или похожий сервис.

Проверить в браузере: открыть `/api/image` — должна открыться картинка,
обновление страницы даёт новую.

## Деплой на Vercel (альтернатива)

[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https%3A%2F%2Fgithub.com%2FMisha1202%2Fmotivation-wallpaper-api&project-name=motivation-wallpaper-api&repository-name=motivation-wallpaper-api)

Адрес: `https://<проект>.vercel.app/api/image`. Если `vercel.app`
блокируется провайдером — используй Render.

## Настройка шортката на iPhone

1. Открой «Команды» → свой шорткат «сменить обои».
2. В действии **«Получить содержимое»** замени URL на
   `https://<service>.onrender.com/api/image`.
3. Остальные действия не меняются: «Установить обои» берёт картинку
   из результата.

Если iOS закеширует ответ, добавь в URL параметр с текущим временем:
`.../api/image?t=` + переменная «Текущая дата» (формат Unix). Но у сервиса
стоит `Cache-Control: no-store`, обычно кеш не мешает.

## Локальный запуск

```bash
pip install -r requirements.txt
python3 api/image.py                 # http://127.0.0.1:8766/api/image
PORT=10000 python3 api/serve.py      # http://127.0.0.1:10000/api/image (как на Render)
```

## Маршруты (`api/serve.py`)

| Путь | Ответ |
| --- | --- |
| `/api/image`, `/image`, `/wallpaper.jpg` | JPEG 1170×2532, без кеша |
| `/health` | `ok` для мониторов |
| `/` | HTML-превью с кнопкой «Новые обои» |

## Как это устроено

- `api/image.py` — рендер: фото/процедурный фон, виньетка, текст с тенью,
  авто-подбор кегля, JPEG q90. При любой ошибке — аварийная картинка.
- `api/serve.py` — HTTP-сервер для Render (порт из `$PORT`).
- `data/quotes.json` — 5305 цитат (собраны из azbyka.ru).
- `fonts/` — PT Serif Bold/Regular (OFL).
- `render.yaml` — Blueprint для Render.
