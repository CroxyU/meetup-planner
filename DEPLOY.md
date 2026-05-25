# Деплой на Render.com

## 1. Подключите Render MCP в Cursor (опционально)

Файл `%USERPROFILE%\.cursor\mcp.json`:

```json
{
  "mcpServers": {
    "render": {
      "url": "https://mcp.render.com/mcp",
      "headers": {
        "Authorization": "Bearer ВАШ_RENDER_API_KEY"
      }
    }
  }
}
```

Ключ: [Render Dashboard → Account → API Keys](https://dashboard.render.com/u/settings#api-keys)

## 2. Репозиторий Git

Render деплоит из GitHub / GitLab / Bitbucket.

```powershell
cd C:\Users\rdd\Projects\meetup-planner
git add .
git commit -m "Initial meetup planner"
# Создайте репозиторий на GitHub и:
git remote add origin https://github.com/ВАШ_ЛОГИН/meetup-planner.git
git push -u origin master
```

## 3. Blueprint на Render (Docker)

Проект собирается через `Dockerfile` (Node + Python), отдельный npm на ПК не нужен.

1. [dashboard.render.com](https://dashboard.render.com) → **New** → **Blueprint**
2. Подключите Git-провайдер и выберите репозиторий `meetup-planner`
3. Render подхватит `render.yaml`
4. Вручную задайте секреты:
   - `BOT_TOKEN` — токен от [@BotFather](https://t.me/BotFather)
   - `WEBAPP_URL` — `https://meetup-planner.onrender.com` (ваш URL сервиса после первого деплоя)

## 4. BotFather

После успешного деплоя:

- **Menu Button / Web App URL:** значение `WEBAPP_URL`
- Проверка: `https://ВАШ-URL.onrender.com/api/health` → `{"status":"ok"}`

## 5. Важно

- **SQLite** на бесплатном Render: данные могут сброситься при пересборке. Для продакшена подключите [Render PostgreSQL](https://render.com/docs/databases) и замените `DATABASE_URL`.
- Токен бота **никогда** не коммитьте — только в переменных Render.
- Free tier «засыпает» без трафика ~15 мин; первый запрос может быть медленным.

## Локальная проверка как на Render

```powershell
cd frontend
npm install && npm run build
cd ..\backend
$env:PORT="8000"
$env:WEBAPP_URL="http://localhost:8000"
bash ../deploy/start.sh
```
