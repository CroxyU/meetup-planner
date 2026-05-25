"""Точка входа FastAPI."""
import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.database import init_db
from app.routers import calendar, groups, proposals, users

logger = logging.getLogger(__name__)


def resolve_frontend_dist() -> Path | None:
    """Ищет собранный Mini App (Docker: /app/frontend/dist)."""
    here = Path(__file__).resolve()
    candidates = [
        here.parents[2] / "frontend" / "dist",
        Path("/app/frontend/dist"),
        here.parents[1].parent / "frontend" / "dist",
    ]
    for path in candidates:
        if (path / "index.html").is_file():
            return path
    return None


FRONTEND_DIST = resolve_frontend_dist()


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    if FRONTEND_DIST:
        logger.info("Mini App static: %s", FRONTEND_DIST)
    else:
        logger.warning("frontend/dist не найден — Mini App по / не откроется")
    yield


app = FastAPI(title="Meetup Planner API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(users.router)
app.include_router(groups.router)
app.include_router(calendar.router)
app.include_router(proposals.router)


@app.get("/api/health")
async def health():
    from app.config import settings

    return {
        "status": "ok",
        "bot_configured": bool(settings.bot_token),
        "webapp_url": settings.webapp_url,
        "static_built": FRONTEND_DIST is not None,
        "static_path": str(FRONTEND_DIST) if FRONTEND_DIST else None,
    }


if FRONTEND_DIST:
    assets_dir = FRONTEND_DIST / "assets"
    if assets_dir.is_dir():
        app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="assets")

    @app.get("/")
    async def serve_index():
        return FileResponse(FRONTEND_DIST / "index.html")

    @app.get("/{page:path}")
    async def spa_fallback(page: str):
        # Не перехватываем API
        if page.startswith("api/"):
            from fastapi import HTTPException

            raise HTTPException(status_code=404)
        file_path = FRONTEND_DIST / page
        if file_path.is_file():
            return FileResponse(file_path)
        return FileResponse(FRONTEND_DIST / "index.html")
