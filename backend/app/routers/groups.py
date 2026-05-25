"""API групп и приглашений."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.deps import get_current_user
from app.models import Group, GroupMember, User, generate_invite_code
from app.schemas import GroupCreate, GroupOut, GroupUpdate, MemberOut
from app.services import member_out_list, require_membership

router = APIRouter(prefix="/api/groups", tags=["groups"])


async def _group_out(db: AsyncSession, group: Group, user: User) -> GroupOut:
    count_result = await db.execute(
        select(func.count()).select_from(GroupMember).where(GroupMember.group_id == group.id)
    )
    return GroupOut(
        id=group.id,
        name=group.name,
        description=group.description,
        invite_code=group.invite_code,
        owner_id=group.owner_id,
        is_owner=group.owner_id == user.id,
        member_count=count_result.scalar() or 0,
    )


@router.get("", response_model=list[GroupOut])
async def list_groups(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Group)
        .join(GroupMember, GroupMember.group_id == Group.id)
        .where(GroupMember.user_id == user.id)
        .order_by(Group.name)
    )
    groups = result.scalars().all()
    return [await _group_out(db, g, user) for g in groups]


@router.post("", response_model=GroupOut)
async def create_group(
    body: GroupCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if user.color is None:
        raise HTTPException(status_code=400, detail="Сначала выберите цвет в настройках")

    group = Group(
        name=body.name,
        description=body.description,
        owner_id=user.id,
        invite_code=generate_invite_code(),
    )
    db.add(group)
    await db.flush()
    db.add(GroupMember(group_id=group.id, user_id=user.id))
    await db.commit()
    await db.refresh(group)
    return await _group_out(db, group, user)


@router.post("/join/{invite_code}", response_model=GroupOut)
async def join_group(
    invite_code: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if user.color is None:
        raise HTTPException(status_code=400, detail="Сначала выберите цвет")

    result = await db.execute(select(Group).where(Group.invite_code == invite_code))
    group = result.scalar_one_or_none()
    if not group:
        raise HTTPException(status_code=404, detail="Группа не найдена")

    existing = await db.execute(
        select(GroupMember).where(
            GroupMember.group_id == group.id,
            GroupMember.user_id == user.id,
        )
    )
    if not existing.scalar_one_or_none():
        db.add(GroupMember(group_id=group.id, user_id=user.id))
        await db.commit()

    return await _group_out(db, group, user)


@router.get("/{group_id}", response_model=GroupOut)
async def get_group(
    group_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await require_membership(db, group_id, user.id)
    result = await db.execute(select(Group).where(Group.id == group_id))
    group = result.scalar_one()
    return await _group_out(db, group, user)


@router.patch("/{group_id}", response_model=GroupOut)
async def update_group(
    group_id: int,
    body: GroupUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Group).where(Group.id == group_id))
    group = result.scalar_one_or_none()
    if not group:
        raise HTTPException(status_code=404)
    if group.owner_id != user.id:
        raise HTTPException(status_code=403, detail="Только владелец может менять группу")

    if body.name is not None:
        group.name = body.name
    if body.description is not None:
        group.description = body.description
    await db.commit()
    await db.refresh(group)
    return await _group_out(db, group, user)


@router.get("/{group_id}/members", response_model=list[MemberOut])
async def list_members(
    group_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await require_membership(db, group_id, user.id)
    result = await db.execute(select(Group).where(Group.id == group_id))
    group = result.scalar_one()
    from app.services import get_group_members

    members = await get_group_members(db, group_id)
    return member_out_list(group, members)


@router.delete("/{group_id}/members/{member_id}")
async def remove_member(
    group_id: int,
    member_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Group).where(Group.id == group_id))
    group = result.scalar_one_or_none()
    if not group or group.owner_id != user.id:
        raise HTTPException(status_code=403)
    if member_id == group.owner_id:
        raise HTTPException(status_code=400, detail="Нельзя удалить владельца")

    await db.execute(
        GroupMember.__table__.delete().where(
            GroupMember.group_id == group_id,
            GroupMember.user_id == member_id,
        )
    )
    await db.commit()
    return {"ok": True}


@router.get("/{group_id}/invite")
async def get_invite_link(
    group_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await require_membership(db, group_id, user.id)
    result = await db.execute(select(Group).where(Group.id == group_id))
    group = result.scalar_one()
    from app.config import settings

    bot_username = settings.webapp_url  # фронт покажет код; deep link через бота
    return {
        "invite_code": group.invite_code,
        "deep_link": f"https://t.me/share/url?url=group_{group.invite_code}",
        "start_param": f"group_{group.invite_code}",
    }
