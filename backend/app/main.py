"""Точка входа FastAPI."""
import asyncio
import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.database import init_db

logger = logging.getLogger(__name__)


def resolve_frontend_dist() -> Path | None:
    here = Path(__file__).resolve()
    for path in (
        here.parents[2] / "frontend" / "dist",
        Path("/app/frontend/dist"),
        here.parents[1].parent / "frontend" / "dist",
    ):
        if (path / "index.html").is_file():
            return path
    return None


FRONTEND_DIST = resolve_frontend_dist()


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    if FRONTEND_DIST:
        logger.info("Mini App: %s", FRONTEND_DIST)
    else:
        logger.error("frontend/dist не найден")

    bot_task = None
    if settings.bot_token:
        mode = (settings.bot_mode or "polling").lower()
        logger.info("BOT_MODE=%s", mode)

        if mode == "webhook":
            from bot.main import run_bot_webhook_mode

            await run_bot_webhook_mode()
        elif mode == "polling":
            from bot.main import run_bot_polling

            bot_task = asyncio.create_task(run_bot_polling())
            logger.info("Бот: polling (локальный режим)")
        else:
            logger.error("Неизвестный BOT_MODE=%s (polling | webhook)", mode)

    yield

    if bot_task:
        bot_task.cancel()
        try:
            await bot_task
        except asyncio.CancelledError:
            pass


app = FastAPI(title="Meetup Planner API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from app.bot_webhook import router as bot_webhook_router  # noqa: E402
from app.routers import calendar, groups, proposals, users  # noqa: E402

app.include_router(bot_webhook_router)
app.include_router(users.router)
app.include_router(groups.router)
app.include_router(calendar.router)
app.include_router(proposals.router)


@app.get("/api/health")
async def health():
    return {
        "status": "ok",
        "bot_configured": bool(settings.bot_token),
        "bot_mode": settings.bot_mode,
        "webapp_url": settings.webapp_url,
        "static_built": FRONTEND_DIST is not None,
        "static_path": str(FRONTEND_DIST) if FRONTEND_DIST else None,
    }


if FRONTEND_DIST:
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIST), html=True), name="static")
