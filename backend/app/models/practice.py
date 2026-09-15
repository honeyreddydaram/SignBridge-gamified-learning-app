from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class PracticeAttempt(Base):
    """
    One logged webcam recognition event — used by both the free-standing
    Recognition module and camera-based Learning challenges, since they share
    the same recognition service. lesson_id is null for free-practice use.
    """

    __tablename__ = "practice_attempts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    lesson_id: Mapped[int | None] = mapped_column(ForeignKey("lessons.id"), nullable=True)

    target_letter: Mapped[str | None] = mapped_column(String(1), nullable=True)
    predicted_letter: Mapped[str | None] = mapped_column(String(1), nullable=True)
    confidence: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    is_correct: Mapped[bool | None] = mapped_column(Boolean, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    user: Mapped["User"] = relationship(back_populates="practice_attempts")  # noqa: F821
