"""API календаря доступности."""
from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.deps import get_current_user
from app.models import User
from app.schemas import AvailabilityUpdate, CalendarMonth, DayDetail
from app.services import build_calendar, build_day_detail, require_membership, set_availability

router = APIRouter(prefix="/api/groups", tags=["calendar"])


@router.get("/{group_id}/calendar", response_model=CalendarMonth)
async def get_calendar(
    group_id: int,
    year: int = Query(...),
    month: int = Query(..., ge=1, le=12),
    only_me: bool = Query(False),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await require_membership(db, group_id, user.id)
    return await build_calendar(db, group_id, year, month, user, only_me=only_me)


@router.get("/{group_id}/days/{day}", response_model=DayDetail)
async def get_day(
    group_id: int,
    day: date,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await require_membership(db, group_id, user.id)
    return await build_day_detail(db, group_id, day)


@router.put("/{group_id}/availability")
async def update_availability(
    group_id: int,
    body: AvailabilityUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await set_availability(db, group_id, user.id, body.days, body.status)
    return {"ok": True}
