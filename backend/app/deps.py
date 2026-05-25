"""Зависимости FastAPI: текущий пользователь из initData."""
from fastapi import Depends, Header
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import validate_telegram_init_data
from app.database import get_db
from app.models import User


async def get_current_user(
    x_telegram_init_data: str = Header(..., alias="X-Telegram-Init-Data"),
    db: AsyncSession = Depends(get_db),
) -> User:
    tg_user = validate_telegram_init_data(x_telegram_init_data)
    tg_id = int(tg_user["id"])

    result = await db.execute(select(User).where(User.tg_id == tg_id))
    user = result.scalar_one_or_none()

    if user is None:
        user = User(
            tg_id=tg_id,
            username=tg_user.get("username"),
            first_name=tg_user.get("first_name") or "Пользователь",
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)

    # Обновляем имя/username при каждом запросе
    user.first_name = tg_user.get("first_name") or user.first_name
    user.username = tg_user.get("username")
    await db.commit()
    await db.refresh(user)
    return user
