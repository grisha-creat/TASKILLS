from datetime import datetime

from sqlalchemy import (
    Boolean, DateTime, ForeignKey, Text, UniqueConstraint, func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..core.db import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(unique=True)
    username: Mapped[str] = mapped_column(unique=True)
    password_hash: Mapped[str]
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    guides: Mapped[list["Guide"]] = relationship(back_populates="author")


class Guide(Base):
    __tablename__ = "guides"

    id: Mapped[int] = mapped_column(primary_key=True)
    author_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    title: Mapped[str]
    description: Mapped[str] = mapped_column(Text, default="")
    is_published: Mapped[bool] = mapped_column(Boolean, default=False)
    forked_from_id: Mapped[int | None] = mapped_column(
        ForeignKey("guides.id"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    author: Mapped["User"] = relationship(back_populates="guides")
    steps: Mapped[list["Step"]] = relationship(
        back_populates="guide", cascade="all, delete-orphan"
    )


class Step(Base):
    __tablename__ = "steps"
    __table_args__ = (UniqueConstraint("guide_id", "position"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    guide_id: Mapped[int] = mapped_column(ForeignKey("guides.id", ondelete="CASCADE"))
    position: Mapped[int]
    title: Mapped[str]
    body: Mapped[str] = mapped_column(Text)

    guide: Mapped["Guide"] = relationship(back_populates="steps")
    completions: Mapped[list["StepCompletion"]] = relationship(
        back_populates="step", cascade="all, delete-orphan"
    )


class StepCompletion(Base):
    __tablename__ = "step_completions"
    __table_args__ = (UniqueConstraint("user_id", "step_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    step_id: Mapped[int] = mapped_column(ForeignKey("steps.id", ondelete="CASCADE"))
    completed_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    step: Mapped["Step"] = relationship(back_populates="completions")


class Comment(Base):
    __tablename__ = "comments"

    id: Mapped[int] = mapped_column(primary_key=True)
    step_id: Mapped[int] = mapped_column(ForeignKey("steps.id", ondelete="CASCADE"))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    text: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class StepVote(Base):
    __tablename__ = "step_votes"
    __table_args__ = (UniqueConstraint("user_id", "step_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    step_id: Mapped[int] = mapped_column(ForeignKey("steps.id", ondelete="CASCADE"))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    is_useful: Mapped[bool] = mapped_column(Boolean)