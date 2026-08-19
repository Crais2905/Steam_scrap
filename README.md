# Steam Scrap API

FastAPI-сервіс для пошуку ігор Steam (Steam Web API) і скрапінгу деталей гри та рецензій (Playwright). Кожен запит логується в БД (таблиця `runs`).

## Вимоги до середовища

- Python 3.11+
- PostgreSQL 13+
- Steam Web API ключ
- ОС Linux/macOS/Windows (для `/games/game/open` потрібен графічний дисплей)

## Встановлення та запуск

```bash
git clone <repo_url>
cd Steam_scrap-main

python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

pip install -r requirements.txt

playwright install --with-deps chromium   # див. нижче

cp .env.example .env            # і заповнити значення (див. "Змінні середовища")

alembic upgrade head

uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Встановлення браузера та системних залежностей

```bash
playwright install --with-deps chromium   # браузер + системні бібліотеки (рекомендовано)
playwright install chromium               # тільки браузер
playwright install-deps chromium          # тільки системні залежності (Linux, потребує sudo)
```

## Змінні середовища (`.env`, за зразком `.env.example`)

| Змінна | Опис | Приклад |
|---|---|---|
| `DATABASE_URL` | Async-підключення до PostgreSQL для застосунку (`asyncpg`) | `postgresql+asyncpg://user:pass@localhost:5432/steam_scrap` |
| `DATABASE_ALEMBIC_URL` | Sync-підключення для Alembic-міграцій (`psycopg2`) | `postgresql+psycopg2://user:pass@localhost:5432/steam_scrap` |
| `STEAM_API_KEY` | Ключ Steam Web API (`x-webapi-key`) | `XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX` |

## Архітектура й основні рішення

- **Шари**: `routes` (HTTP) → `services` (бізнес-логіка) → `repositories` (доступ до БД); окремо `scrapers` (Playwright-логіка) та `db` (SQLAlchemy engine/session/моделі).
- **Два джерела даних**: `SteamAPIService` — швидкий пошук через офіційний Steam Web API; `PlaywrightSteamScraper` — скрапінг сторінки магазину для деталей і рецензій, яких API не дає.
- **Browser lifecycle**: один headless- і один видимий (non-headless) браузер Chromium піднімаються один раз при старті застосунку (`app/main.py`, FastAPI `lifespan`) через `SteamScraperFactory` і перевикористовуються для всіх запитів. Для `/games/details` на кожен запит створюється ізольований `BrowserContext`; `/games/game/open` навмисно відкриває видимий браузер.
- **Локалізація й вік-гейт**: контекст браузера створюється з `locale="uk-UA"` і заголовком `Accept-Language`, а також попередньо виставленими cookies (`steamCountry`, `wants_mature_content`, `birthtime`), щоб одразу обійти вікове підтвердження Steam.
- **Аудит запитів**: кожен виклик (HTTP до Steam API або скрапінг) обгортається try/except і незалежно від результату пишеться в таблицю `runs` через `RunsRepo` — `method_type` (`http`/`headless`/`non_headless`), вхід/вихід, `status` (`completed`/`failed`), час початку/кінця. Історія доступна через `/runs`.
- **Стек повністю асинхронний**: FastAPI + SQLAlchemy 2.0 async ORM (`asyncpg`) + Playwright async API.
- **Alembic** використовує окрему sync-строку підключення (`DATABASE_ALEMBIC_URL`), бо міграції виконуються поза event loop застосунку.

## Endpoint-и

| Метод | Шлях | Параметри | Опис |
|---|---|---|---|
| GET | `/health/` | — | Перевірка живості сервісу |
| GET | `/games/search` | `query` (str, required), `limit` (int, 1–20, default 10) | Пошук ігор через Steam Web API |
| GET | `/games/details` | `game_name` (str, required), `reviews_count` (int, default 3) | Скрапінг деталей гри + рецензії |
| POST | `/games/game/open` | `game_name` (str, required) | Знайти гру і відкрити її у видимому браузері |
| GET | `/runs/` | `offset` (int, default 0), `limit` (int, default 10) | Список запусків з пагінацією |
| GET | `/runs/{run_id}` | `run_id` (int, path) | Деталі конкретного запуску |

## Приклади запитів

### curl

```bash
# Health check
curl -X GET "http://localhost:8000/health/"

# Пошук ігор
curl -X GET "http://localhost:8000/games/search?query=Half-Life&limit=5"

# Деталі гри
curl -X GET "http://localhost:8000/games/details?game_name=Half-Life%202&reviews_count=3"

# Відкрити гру у видимому браузері
curl -X POST "http://localhost:8000/games/game/open?game_name=Half-Life%202"

# Список запусків
curl -X GET "http://localhost:8000/runs/?offset=0&limit=10"

# Деталі запуску
curl -X GET "http://localhost:8000/runs/1"
```