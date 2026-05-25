# Meetup Planner — Telegram Bot + Mini App

Планирование встреч в группах друзей: общий календарь доступности, цветовые статусы, предложения встреч с уведомлениями в боте.

## Архитектура

```
┌─────────────────┐     initData      ┌──────────────────┐
│  Telegram Mini  │ ────────────────► │  FastAPI (API)   │
│  App (Vue 3)    │                   │  SQLAlchemy DB   │
└─────────────────┘                   └────────┬─────────┘
                                               │
┌─────────────────┐     polling       ┌────────▼─────────┐
│  Telegram User  │ ◄──────────────── │  aiogram 3 Bot   │
└─────────────────┘                   └──────────────────┘
```

| Компонент | Технологии |
|-----------|------------|
| Mini App | Vue 3, Vite, Telegram WebApp SDK |
| API | FastAPI, async SQLAlchemy, SQLite |
| Бот | aiogram 3, уведомления, inline-кнопки |
| Auth | Проверка подписи `initData` (без отдельного JWT) |

### Таблицы БД

- `users` — tg_id, цвет, имя
- `groups` — название, invite_code, owner
- `group_members` — связь пользователь ↔ группа
- `availabilities` — статус дня (free/busy) по группе
- `proposals`, `proposal_dates`, `proposal_votes`

## Быстрый старт (локально)

### 1. Переменные окружения

Скопируйте `.env.example` в `.env` в корне проекта:

```env
BOT_TOKEN=ваш_токен_от_BotFather
WEBAPP_URL=https://ваш-публичный-url   # для продакшена; локально http://localhost:5173
API_PORT=8000
DATABASE_URL=sqlite+aiosqlite:///./meetup.db
```

> **Безопасность:** не коммитьте `.env`. Если токен попал в чат — отзовите его в [@BotFather](https://t.me/BotFather) и выпустите новый.

### 2. Backend

```powershell
cd C:\Users\rdd\Projects\meetup-planner\backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python run_api.py
```

### 3. Бот (второй терминал)

```powershell
cd C:\Users\rdd\Projects\meetup-planner\backend
.\.venv\Scripts\Activate.ps1
python -m bot.main
```

### 4. Mini App

```powershell
cd C:\Users\rdd\Projects\meetup-planner\frontend
npm install
npm run dev
```

В [@BotFather](https://t.me/BotFather) укажите Web App URL: `http://localhost:5173` (для теста нужен HTTPS-туннель, например ngrok).

### 5. Продакшен

1. `npm run build` в `frontend/`
2. FastAPI отдаёт `frontend/dist/` как статику
3. `WEBAPP_URL` — HTTPS-адрес вашего сервера
4. Menu Button / Web App в настройках бота

## Приглашение в группу

Участники переходят по ссылке бота:

```
/start group_<invite_code>
```

Код отображается во вкладке «Участники» → «Скопировать приглашение».

## UX-функции

- Тап по дню — трёхпозиционный тогл: пусто → свободен → занят → пусто (1–2 касания)
- Режим «кисти»: Свободен / Занят + тап по дням
- Режим «Даты» + кнопка «Предложить» для встречи
- Долгое нажатие (500 мс) — детали дня и списки участников
- Свайп влево/вправо — смена месяца
- Подсветка дней, когда все свободны
- Переключатель «Все / Только я»
- Тема Telegram (светлая/тёмная) через CSS-переменные

## API (кратко)

| Метод | Путь | Описание |
|-------|------|----------|
| GET | `/api/users/me` | Профиль |
| PATCH | `/api/users/me/color` | Цвет |
| GET/POST | `/api/groups` | Список / создание |
| POST | `/api/groups/join/{code}` | Вступление |
| GET | `/api/groups/{id}/calendar` | Календарь месяца |
| PUT | `/api/groups/{id}/availability` | Статусы дней |
| POST | `/api/groups/{id}/proposals` | Предложение встречи |

Все запросы требуют заголовок `X-Telegram-Init-Data`.

## Деплой на Render

Пошаговая инструкция: **[DEPLOY.md](./DEPLOY.md)** (Docker + `render.yaml`).

## Лицензия

MIT — используйте свободно для своих проектов.
