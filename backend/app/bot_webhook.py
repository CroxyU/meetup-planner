"""HTTP webhook для Telegram (режим bot_mode=webhook)."""
from fastapi import APIRouter, Request
from aiogram.types import Update

from bot.main import bot, dp

router = APIRouter(tags=["telegram"])


@router.post("/webhook/telegram")
async def telegram_webhook(request: Request) -> dict:
    payload = await request.json()
    update = Update.model_validate(payload)
    await dp.feed_update(bot, update)
    return {"ok": True}
