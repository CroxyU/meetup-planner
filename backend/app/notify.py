"""Отправка уведомлений через Telegram Bot API."""
from datetime import date

import httpx

from app.calendar_utils import format_dates_ru
from app.config import settings
from app.database import async_session
from app.models import GroupMember, User
from sqlalchemy import select


async def _send_message(tg_id: int, text: str, reply_markup: dict | None = None) -> None:
    url = f"https://api.telegram.org/bot{settings.bot_token}/sendMessage"
    payload: dict = {"chat_id": tg_id, "text": text, "parse_mode": "HTML"}
    if reply_markup:
        payload["reply_markup"] = reply_markup
    async with httpx.AsyncClient(timeout=15) as client:
        await client.post(url, json=payload)


def _inline_keyboard(proposal_id: int, group_id: int) -> dict:
    webapp = settings.webapp_url
    return {
        "inline_keyboard": [
            [
                {"text": "✅ Свободен", "callback_data": f"vote:{proposal_id}:free"},
                {"text": "❌ Занят", "callback_data": f"vote:{proposal_id}:busy"},
            ],
            [
                {
                    "text": "📅 Открыть в приложении",
                    "web_app": {"url": f"{webapp}?group={group_id}&tab=proposals"},
                }
            ],
        ]
    }


async def notify_proposal_created(
    group_id: int,
    proposer_name: str,
    title: str,
    days: list[date],
    proposal_id: int,
    exclude_tg_id: int | None = None,
) -> None:
    dates_str = format_dates_ru(days)
    text = (
        f"<b>{proposer_name}</b> предлагает встречу «<b>{title}</b>» "
        f"на {dates_str}.\n\n"
        "Ты можешь подтвердить или изменить свой статус:"
    )
    markup = _inline_keyboard(proposal_id, group_id)

    async with async_session() as db:
        result = await db.execute(
            select(User.tg_id)
            .join(GroupMember, GroupMember.user_id == User.id)
            .where(GroupMember.group_id == group_id)
        )
        tg_ids = [row[0] for row in result.all()]

    for tg_id in tg_ids:
        if exclude_tg_id and tg_id == exclude_tg_id:
            continue
        try:
            await _send_message(tg_id, text, markup)
        except Exception:
            pass
