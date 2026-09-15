from datetime import date, datetime, timezone

from sqlalchemy import Date, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Gamification state lives directly on the user row because it is 1:1 —
    # a separate table would just be a join on every request.
    xp_total: Mapped[int] = mapped_column(Integer, default=0)
    level: Mapped[int] = mapped_column(Integer, default=1)
    hearts: Mapped[int] = mapped_column(Integer, default=5)
    hearts_last_refill_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    current_streak: Mapped[int] = mapped_column(Integer, default=0)
    longest_streak: Mapped[int] = mapped_column(Integer, default=0)
    last_activity_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    lesson_progress: Mapped[list["UserLessonProgress"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    xp_transactions: Mapped[list["XPTransaction"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    achievements: Mapped[list["UserAchievement"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    practice_attempts: Mapped[list["PracticeAttempt"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    sign_mastery: Mapped[list["UserSignMastery"]] = relationship(  # noqa: F821
        back_populates="user", cascade="all, delete-orphan"
    )
    quest_progress: Mapped[list["UserQuestProgress"]] = relationship(  # noqa: F821
        back_populates="user", cascade="all, delete-orphan"
    )
