"""Модели SQLAlchemy."""
import enum
import secrets
from datetime import date, datetime

from sqlalchemy import (
    BigInteger,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class AvailabilityStatus(str, enum.Enum):
    free = "free"
    busy = "busy"


class VoteStatus(str, enum.Enum):
    free = "free"
    busy = "busy"


def generate_invite_code() -> str:
    return secrets.token_urlsafe(8)[:10]


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    tg_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True)
    username: Mapped[str | None] = mapped_column(String(64))
    first_name: Mapped[str] = mapped_column(String(128), default="")
    color: Mapped[str | None] = mapped_column(String(7))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    memberships: Mapped[list["GroupMember"]] = relationship(back_populates="user")
    availabilities: Mapped[list["Availability"]] = relationship(back_populates="user")
    proposals: Mapped[list["Proposal"]] = relationship(back_populates="proposer")


class Group(Base):
    __tablename__ = "groups"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(128))
    description: Mapped[str | None] = mapped_column(Text)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    invite_code: Mapped[str] = mapped_column(String(16), unique=True, default=generate_invite_code)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    owner: Mapped["User"] = relationship(foreign_keys=[owner_id])
    members: Mapped[list["GroupMember"]] = relationship(back_populates="group", cascade="all, delete-orphan")
    availabilities: Mapped[list["Availability"]] = relationship(back_populates="group", cascade="all, delete-orphan")
    proposals: Mapped[list["Proposal"]] = relationship(back_populates="group", cascade="all, delete-orphan")


class GroupMember(Base):
    __tablename__ = "group_members"
    __table_args__ = (UniqueConstraint("group_id", "user_id", name="uq_group_user"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    group_id: Mapped[int] = mapped_column(ForeignKey("groups.id", ondelete="CASCADE"))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    joined_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    group: Mapped["Group"] = relationship(back_populates="members")
    user: Mapped["User"] = relationship(back_populates="memberships")


class Availability(Base):
    __tablename__ = "availabilities"
    __table_args__ = (UniqueConstraint("user_id", "group_id", "day", name="uq_avail"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    group_id: Mapped[int] = mapped_column(ForeignKey("groups.id", ondelete="CASCADE"))
    day: Mapped[date] = mapped_column(Date)
    status: Mapped[AvailabilityStatus] = mapped_column(Enum(AvailabilityStatus))

    user: Mapped["User"] = relationship(back_populates="availabilities")
    group: Mapped["Group"] = relationship(back_populates="availabilities")


class Proposal(Base):
    __tablename__ = "proposals"

    id: Mapped[int] = mapped_column(primary_key=True)
    group_id: Mapped[int] = mapped_column(ForeignKey("groups.id", ondelete="CASCADE"))
    proposer_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    title: Mapped[str] = mapped_column(String(256))
    description: Mapped[str | None] = mapped_column(Text)
    place: Mapped[str | None] = mapped_column(String(256))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    group: Mapped["Group"] = relationship(back_populates="proposals")
    proposer: Mapped["User"] = relationship(back_populates="proposals")
    dates: Mapped[list["ProposalDate"]] = relationship(back_populates="proposal", cascade="all, delete-orphan")
    votes: Mapped[list["ProposalVote"]] = relationship(back_populates="proposal", cascade="all, delete-orphan")


class ProposalDate(Base):
    __tablename__ = "proposal_dates"

    id: Mapped[int] = mapped_column(primary_key=True)
    proposal_id: Mapped[int] = mapped_column(ForeignKey("proposals.id", ondelete="CASCADE"))
    day: Mapped[date] = mapped_column(Date)

    proposal: Mapped["Proposal"] = relationship(back_populates="dates")


class ProposalVote(Base):
    __tablename__ = "proposal_votes"
    __table_args__ = (UniqueConstraint("proposal_id", "user_id", name="uq_vote"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    proposal_id: Mapped[int] = mapped_column(ForeignKey("proposals.id", ondelete="CASCADE"))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    status: Mapped[VoteStatus] = mapped_column(Enum(VoteStatus))

    proposal: Mapped["Proposal"] = relationship(back_populates="votes")
    user: Mapped["User"] = relationship()
