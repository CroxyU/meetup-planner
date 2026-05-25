"""Бизнес-логика: членство в группе, календарь, уведомления."""
from datetime import date

from fastapi import HTTPException
from sqlalchemy import and_, delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.calendar_utils import month_grid
from app.models import (
    Availability,
    AvailabilityStatus,
    Group,
    GroupMember,
    Proposal,
    ProposalDate,
    ProposalVote,
    User,
)
from app.schemas import CalendarDay, CalendarMonth, DayMemberStatus, DayDetail, MemberOut


async def require_membership(db: AsyncSession, group_id: int, user_id: int) -> GroupMember:
    result = await db.execute(
        select(GroupMember).where(
            GroupMember.group_id == group_id,
            GroupMember.user_id == user_id,
        )
    )
    member = result.scalar_one_or_none()
    if not member:
        raise HTTPException(status_code=403, detail="Вы не участник этой группы")
    return member


async def get_group_members(db: AsyncSession, group_id: int) -> list[User]:
    result = await db.execute(
        select(User)
        .join(GroupMember, GroupMember.user_id == User.id)
        .where(GroupMember.group_id == group_id)
    )
    return list(result.scalars().all())


async def build_calendar(
    db: AsyncSession,
    group_id: int,
    year: int,
    month: int,
    current_user: User,
    only_me: bool = False,
) -> CalendarMonth:
    members = await get_group_members(db, group_id)
    member_ids = [m.id for m in members]

    # Диапазон дней сетки (включая соседние месяцы)
    grid = month_grid(year, month)
    if not grid:
        return CalendarMonth(year=year, month=month, days=[])

    start_day, end_day = grid[0][0], grid[-1][0]

    result = await db.execute(
        select(Availability).where(
            Availability.group_id == group_id,
            Availability.user_id.in_(member_ids),
            Availability.day >= start_day,
            Availability.day <= end_day,
        )
    )
    avails = result.scalars().all()
    # avail_map[(day, user_id)] = status
    avail_map: dict[tuple[date, int], AvailabilityStatus] = {
        (a.day, a.user_id): a.status for a in avails
    }

    today = date.today()
    days_out: list[CalendarDay] = []

    for d, is_current in grid:
        member_statuses: list[DayMemberStatus] = []
        free_count = 0
        marked_count = 0

        for m in members:
            if only_me and m.id != current_user.id:
                continue
            st = avail_map.get((d, m.id))
            member_statuses.append(
                DayMemberStatus(
                    user_id=m.id,
                    first_name=m.first_name,
                    color=m.color,
                    status=st,
                )
            )
            if st == AvailabilityStatus.free:
                free_count += 1
                marked_count += 1
            elif st == AvailabilityStatus.busy:
                marked_count += 1

        all_free = (
            not only_me
            and len(members) > 0
            and free_count == len(members)
            and marked_count == len(members)
        )

        my_status = avail_map.get((d, current_user.id))

        days_out.append(
            CalendarDay(
                day=d,
                is_current_month=is_current,
                is_today=d == today,
                all_free=all_free,
                my_status=my_status,
                members=member_statuses if not only_me else member_statuses,
            )
        )

    return CalendarMonth(year=year, month=month, days=days_out)


async def build_day_detail(
    db: AsyncSession,
    group_id: int,
    day: date,
) -> DayDetail:
    members = await get_group_members(db, group_id)
    member_ids = [m.id for m in members]

    result = await db.execute(
        select(Availability).where(
            Availability.group_id == group_id,
            Availability.day == day,
            Availability.user_id.in_(member_ids),
        )
    )
    avails = {a.user_id: a.status for a in result.scalars().all()}

    statuses: list[DayMemberStatus] = []
    free, busy, unmarked = [], [], []

    for m in members:
        st = avails.get(m.id)
        item = DayMemberStatus(
            user_id=m.id,
            first_name=m.first_name,
            color=m.color,
            status=st,
        )
        statuses.append(item)
        if st == AvailabilityStatus.free:
            free.append(item)
        elif st == AvailabilityStatus.busy:
            busy.append(item)
        else:
            unmarked.append(item)

    all_free = len(members) > 0 and len(free) == len(members)

    return DayDetail(
        day=day,
        members=statuses,
        all_free=all_free,
        free=free,
        busy=busy,
        unmarked=unmarked,
    )


async def set_availability(
    db: AsyncSession,
    group_id: int,
    user_id: int,
    days: list[date],
    status: AvailabilityStatus | None,
) -> None:
    await require_membership(db, group_id, user_id)

    for day in days:
        result = await db.execute(
            select(Availability).where(
                Availability.group_id == group_id,
                Availability.user_id == user_id,
                Availability.day == day,
            )
        )
        existing = result.scalar_one_or_none()

        if status is None:
            if existing:
                await db.delete(existing)
        elif existing:
            existing.status = status
        else:
            db.add(
                Availability(
                    group_id=group_id,
                    user_id=user_id,
                    day=day,
                    status=status,
                )
            )
    await db.commit()


def member_out_list(group: Group, members: list[User]) -> list[MemberOut]:
    return [
        MemberOut(
            id=m.id,
            first_name=m.first_name,
            username=m.username,
            color=m.color,
            is_owner=m.id == group.owner_id,
        )
        for m in members
    ]
