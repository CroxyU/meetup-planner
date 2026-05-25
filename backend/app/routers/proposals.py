"""API предложений встреч."""
import asyncio

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.deps import get_current_user
from app.models import Proposal, ProposalDate, ProposalVote, User, VoteStatus
from app.schemas import ProposalCreate, ProposalOut, ProposalVoteOut, VoteUpdate
from app.services import get_group_members, require_membership

router = APIRouter(prefix="/api", tags=["proposals"])


def _proposal_to_out(proposal: Proposal, members: list[User], current: User) -> ProposalOut:
    member_map = {m.id: m for m in members}
    vote_map = {v.user_id: v.status for v in proposal.votes}
    votes_out = [
        ProposalVoteOut(
            user_id=m.id,
            first_name=m.first_name,
            color=m.color,
            status=vote_map.get(m.id),
        )
        for m in members
    ]
    return ProposalOut(
        id=proposal.id,
        title=proposal.title,
        description=proposal.description,
        place=proposal.place,
        proposer_name=proposal.proposer.first_name,
        created_at=proposal.created_at,
        days=sorted(d.day for d in proposal.dates),
        votes=votes_out,
        my_vote=vote_map.get(current.id),
    )


@router.get("/groups/{group_id}/proposals", response_model=list[ProposalOut])
async def list_proposals(
    group_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await require_membership(db, group_id, user.id)
    result = await db.execute(
        select(Proposal)
        .where(Proposal.group_id == group_id)
        .options(
            selectinload(Proposal.dates),
            selectinload(Proposal.votes),
            selectinload(Proposal.proposer),
        )
        .order_by(Proposal.created_at.desc())
    )
    proposals = result.scalars().all()
    members = await get_group_members(db, group_id)
    return [_proposal_to_out(p, members, user) for p in proposals]


@router.post("/groups/{group_id}/proposals", response_model=ProposalOut)
async def create_proposal(
    group_id: int,
    body: ProposalCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await require_membership(db, group_id, user.id)

    proposal = Proposal(
        group_id=group_id,
        proposer_id=user.id,
        title=body.title,
        description=body.description,
        place=body.place,
    )
    db.add(proposal)
    await db.flush()
    for d in body.days:
        db.add(ProposalDate(proposal_id=proposal.id, day=d))
    await db.commit()

    result = await db.execute(
        select(Proposal)
        .where(Proposal.id == proposal.id)
        .options(
            selectinload(Proposal.dates),
            selectinload(Proposal.votes),
            selectinload(Proposal.proposer),
        )
    )
    proposal = result.scalar_one()
    members = await get_group_members(db, group_id)

    # Уведомление участникам через бота (фоново)
    from app.notify import notify_proposal_created

    asyncio.create_task(
        notify_proposal_created(
            group_id=group_id,
            proposer_name=user.first_name,
            title=body.title,
            days=body.days,
            proposal_id=proposal.id,
            exclude_tg_id=user.tg_id,
        )
    )

    return _proposal_to_out(proposal, members, user)


@router.patch("/proposals/{proposal_id}/vote", response_model=ProposalOut)
async def vote_proposal(
    proposal_id: int,
    body: VoteUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Proposal)
        .where(Proposal.id == proposal_id)
        .options(
            selectinload(Proposal.dates),
            selectinload(Proposal.votes),
            selectinload(Proposal.proposer),
        )
    )
    proposal = result.scalar_one_or_none()
    if not proposal:
        raise HTTPException(status_code=404)

    await require_membership(db, proposal.group_id, user.id)

    existing = next((v for v in proposal.votes if v.user_id == user.id), None)
    if existing:
        existing.status = body.status
    else:
        db.add(ProposalVote(proposal_id=proposal.id, user_id=user.id, status=body.status))
    await db.commit()
    await db.refresh(proposal)

    members = await get_group_members(db, proposal.group_id)
    return _proposal_to_out(proposal, members, user)
