from datetime import datetime, timezone
from enum import Enum as PyEnum

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class LessonStatus(str, PyEnum):
    LOCKED = "locked"
    UNLOCKED = "unlocked"
    COMPLETED = "completed"


class LessonType(str, PyEnum):
    ALPHABET = "alphabet"  # one lesson per A-Z letter
    VOCABULARY = "vocabulary"  # one lesson per thematic word category (see curriculum.py)


class Lesson(Base):
    """
    Two independent, separately-unlocking tracks share this table:
      - alphabet: 26 rows, one per letter, order_index 1-26
      - vocabulary: one row per thematic category built from the verified
        114-word sign manifest (ml/word_signs_verified.json), order_index 1-N
    order_index is only unique WITHIN a lesson_type (see __table_args__) so
    both tracks can each start their own numbering at 1 and unlock
    independently — completing the alphabet is not a prerequisite for
    starting vocabulary, or vice versa.
    """

    __tablename__ = "lessons"
    __table_args__ = (UniqueConstraint("lesson_type", "order_index", name="uq_lesson_type_order"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    lesson_type: Mapped[LessonType] = mapped_column(Enum(LessonType), nullable=False, default=LessonType.ALPHABET)
    letter: Mapped[str | None] = mapped_column(String(1), unique=True, nullable=True)
    concept_key: Mapped[str | None] = mapped_column(String(50), unique=True, nullable=True)
    order_index: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(String(500), nullable=False, default="")

    progress: Mapped[list["UserLessonProgress"]] = relationship(back_populates="lesson")


class UserLessonProgress(Base):
    __tablename__ = "user_lesson_progress"
    __table_args__ = (UniqueConstraint("user_id", "lesson_id", name="uq_user_lesson"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    lesson_id: Mapped[int] = mapped_column(ForeignKey("lessons.id"), nullable=False)

    status: Mapped[LessonStatus] = mapped_column(
        Enum(LessonStatus), default=LessonStatus.LOCKED, nullable=False
    )
    best_score_pct: Mapped[int] = mapped_column(Integer, default=0)
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)

    user: Mapped["User"] = relationship(back_populates="lesson_progress")  # noqa: F821
    lesson: Mapped["Lesson"] = relationship(back_populates="progress")
