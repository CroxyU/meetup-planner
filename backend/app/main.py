"""Точка входа FastAPI."""
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.database import init_db
from app.routers import calendar, groups, proposals, users


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
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
    return {"status": "ok"}


# Статика Mini App после сборки (npm run build)
_root = Path(__file__).resolve().parents[2]
_dist = _root / "frontend" / "dist"
if not _dist.exists():
    _dist = _root.parent / "frontend" / "dist"  # запасной путь
if _dist.exists():
    app.mount("/", StaticFiles(directory=str(_dist), html=True), name="static")
