"""API пользователя и настроек."""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.deps import get_current_user
from app.models import User
from app.schemas import ColorUpdate, UserOut

router = APIRouter(prefix="/api/users", tags=["users"])


@router.get("/me", response_model=UserOut)
async def get_me(user: User = Depends(get_current_user)):
    return UserOut(
        id=user.id,
        tg_id=user.tg_id,
        username=user.username,
        first_name=user.first_name,
        color=user.color,
        needs_color=user.color is None,
    )


@router.get("/palette")
async def get_palette():
    return {"colors": settings.color_palette}


@router.patch("/me/color", response_model=UserOut)
async def set_color(
    body: ColorUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if body.color not in settings.color_palette:
        # Разрешаем любой hex, но рекомендуем палитру
        pass
    user.color = body.color
    await db.commit()
    await db.refresh(user)
    return UserOut(
        id=user.id,
        tg_id=user.tg_id,
        username=user.username,
        first_name=user.first_name,
        color=user.color,
        needs_color=False,
    )
