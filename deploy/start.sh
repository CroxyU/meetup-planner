#!/usr/bin/env bash
# API (uvicorn) + бот (polling) в одном контейнере Render
set -euo pipefail
# Docker: /app/backend; локально: .../backend
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
if [ -d "$SCRIPT_DIR/../backend" ]; then
  cd "$SCRIPT_DIR/../backend"
else
  cd /app/backend
fi

mkdir -p data
export PORT="${PORT:-8000}"

echo "==> Starting Telegram bot (background)"
python -m bot.main &
BOT_PID=$!

cleanup() {
  kill "$BOT_PID" 2>/dev/null || true
}
trap cleanup EXIT

echo "==> Starting API on port $PORT"
exec uvicorn app.main:app --host 0.0.0.0 --port "$PORT"
