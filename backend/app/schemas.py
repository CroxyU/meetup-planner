"""Pydantic-схемы API."""
from datetime import date, datetime

from pydantic import BaseModel, Field

from app.models import AvailabilityStatus, VoteStatus


class UserOut(BaseModel):
    id: int
    tg_id: int
    username: str | None
    first_name: str
    color: str | None
    needs_color: bool = False

    model_config = {"from_attributes": True}


class ColorUpdate(BaseModel):
    color: str = Field(pattern=r"^#[0-9A-Fa-f]{6}$")


class GroupCreate(BaseModel):
    name: str = Field(min_length=1, max_length=128)
    description: str | None = None


class GroupUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=128)
    description: str | None = None


class GroupOut(BaseModel):
    id: int
    name: str
    description: str | None
    invite_code: str
    owner_id: int
    is_owner: bool = False
    member_count: int = 0

    model_config = {"from_attributes": True}


class MemberOut(BaseModel):
    id: int
    first_name: str
    username: str | None
    color: str | None
    is_owner: bool = False

    model_config = {"from_attributes": True}


class DayMemberStatus(BaseModel):
    user_id: int
    first_name: str
    color: str | None
    status: AvailabilityStatus | None


class DayDetail(BaseModel):
    day: date
    members: list[DayMemberStatus]
    all_free: bool
    free: list[DayMemberStatus]
    busy: list[DayMemberStatus]
    unmarked: list[DayMemberStatus]


class CalendarDay(BaseModel):
    day: date
    is_current_month: bool
    is_today: bool
    all_free: bool
    my_status: AvailabilityStatus | None
    members: list[DayMemberStatus]


class CalendarMonth(BaseModel):
    year: int
    month: int
    days: list[CalendarDay]


class AvailabilityUpdate(BaseModel):
    days: list[date]
    status: AvailabilityStatus | None  # None = сбросить отметку


class ProposalCreate(BaseModel):
    title: str = Field(min_length=1, max_length=256)
    description: str | None = None
    place: str | None = None
    days: list[date] = Field(min_length=1)


class ProposalDateOut(BaseModel):
    day: date

    model_config = {"from_attributes": True}


class ProposalVoteOut(BaseModel):
    user_id: int
    first_name: str
    color: str | None
    status: VoteStatus | None

    model_config = {"from_attributes": True}


class ProposalOut(BaseModel):
    id: int
    title: str
    description: str | None
    place: str | None
    proposer_name: str
    created_at: datetime
    days: list[date]
    votes: list[ProposalVoteOut]
    my_vote: VoteStatus | None = None

    model_config = {"from_attributes": True}


class VoteUpdate(BaseModel):
    status: VoteStatus
