#!/usr/bin/env bash
# Сборка на Render: фронт + зависимости Python
set -euo pipefail
cd "$(dirname "$0")/.."

echo "==> Node + frontend build"
cd frontend
if command -v npm >/dev/null 2>&1; then
  npm ci || npm install
  npm run build
else
  echo "npm not in PATH, trying corepack..."
  corepack enable 2>/dev/null || true
  npm ci || npm install
  npm run build
fi
cd ..

echo "==> Python dependencies"
cd backend
pip install -r requirements.txt
mkdir -p data
cd ..

echo "==> Build OK"
