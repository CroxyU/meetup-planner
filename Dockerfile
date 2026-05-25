# API + Mini App + бот в одном образе
FROM node:20-alpine AS frontend
WORKDIR /build/frontend
COPY frontend/package.json ./
RUN npm install
COPY frontend/ ./
RUN npm run build

FROM python:3.12-slim
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends bash \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt ./backend/
RUN pip install --no-cache-dir -r backend/requirements.txt

COPY backend/ ./backend/
COPY --from=frontend /build/frontend/dist ./frontend/dist
COPY deploy/start.sh ./deploy/start.sh
RUN chmod +x ./deploy/start.sh && mkdir -p ./backend/data

ENV PYTHONUNBUFFERED=1
WORKDIR /app/backend
EXPOSE 8000

CMD ["bash", "/app/deploy/start.sh"]
