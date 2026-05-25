#!/usr/bin/env bash
# Только uvicorn — бот стартует внутри FastAPI (app.main lifespan)
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
if [ -d "$SCRIPT_DIR/../backend" ]; then
  cd "$SCRIPT_DIR/../backend"
else
  cd /app/backend
fi

mkdir -p data
export PORT="${PORT:-8000}"

echo "==> API + bot (single process) on port $PORT"
exec uvicorn app.main:app --host 0.0.0.0 --port "$PORT" --workers 1
