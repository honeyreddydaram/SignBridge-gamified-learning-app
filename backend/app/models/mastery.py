from datetime import date, datetime, timezone
from enum import Enum as PyEnum

from sqlalchemy import Date, DateTime, Enum, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class MasteryState(str, PyEnum):
    NEW = "new"
    LEARNING = "learning"
    PRACTICING = "practicing"
    MASTERED = "mastered"


class UserSignMastery(Base):
    """
    Per-user, per-word mastery tracking for the vocabulary Learn -> Recognize
    -> Produce -> Recall -> Master loop. `word` is the normalized key
    matching app.asl_signs.SUPPORTED_SIGNS (e.g. "HELLO", "THANKYOU") — not a
    foreign key, since vocabulary words are static reference data (like
    Lesson.letter), not a DB-owned entity.

    State machine (see mastery_service.py for the actual transition logic —
    documented there, kept deliberately simple):
      NEW        -> default; no recorded interaction yet
      LEARNING   -> at least one interaction recorded (viewed the demo, or
                    attempted the Recognize quiz)
      PRACTICING -> >=2 correct Recognize answers AND >=1 Produce self-check
      MASTERED   -> a successful Recall self-check (blind production, no
                    demo shown) recorded on a DIFFERENT calendar day than at
                    least one earlier interaction — this is the "can't just
                    click through once" requirement: distinct_days_interacted
                    must be >=2 at the moment of the qualifying Recall.
    MASTERED is sticky (never downgrades) once reached.
    """

    __tablename__ = "user_sign_mastery"
    __table_args__ = (UniqueConstraint("user_id", "word", name="uq_user_sign_mastery_word"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    word: Mapped[str] = mapped_column(String(50), nullable=False)

    state: Mapped[MasteryState] = mapped_column(Enum(MasteryState), default=MasteryState.NEW, nullable=False)

    recognize_attempt_count: Mapped[int] = mapped_column(Integer, default=0)
    recognize_correct_count: Mapped[int] = mapped_column(Integer, default=0)
    produce_selfcheck_count: Mapped[int] = mapped_column(Integer, default=0)
    recall_selfcheck_count: Mapped[int] = mapped_column(Integer, default=0)

    distinct_days_interacted: Mapped[int] = mapped_column(Integer, default=0)
    last_interaction_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    mastered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)

    user: Mapped["User"] = relationship(back_populates="sign_mastery")  # noqa: F821


class QuestType(str, PyEnum):
    MISSION = "mission"  # a checklist of words to sign, one at a time
    SCENARIO = "scenario"  # a short situational prompt expecting one concept


class Quest(Base):
    """
    Static, seeded quest catalog — data-driven like curriculum.py's
    VOCABULARY_CATEGORIES, so new quests are added as data, not new screens.
    `words_json` is a JSON-encoded list (order matters, e.g. '["HELLO",
    "PLEASE", "THANKYOU"]') rather than a join table — quests are small,
    static, ordered lists, not a relation that needs independent querying.
    """

    __tablename__ = "quests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    quest_key: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    quest_type: Mapped[QuestType] = mapped_column(Enum(QuestType), nullable=False, default=QuestType.MISSION)
    title: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(String(500), nullable=False, default="")
    prompt: Mapped[str | None] = mapped_column(String(300), nullable=True)
    words_json: Mapped[str] = mapped_column(String(1000), nullable=False)
    order_index: Mapped[int] = mapped_column(Integer, nullable=False, unique=True)

    progress: Mapped[list["UserQuestProgress"]] = relationship(back_populates="quest")


class UserQuestProgress(Base):
    __tablename__ = "user_quest_progress"
    __table_args__ = (UniqueConstraint("user_id", "quest_id", name="uq_user_quest"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    quest_id: Mapped[int] = mapped_column(ForeignKey("quests.id"), nullable=False)

    completed_words_json: Mapped[str] = mapped_column(String(1000), nullable=False, default="[]")
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="in_progress")  # in_progress | completed
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)

    user: Mapped["User"] = relationship(back_populates="quest_progress")  # noqa: F821
    quest: Mapped["Quest"] = relationship(back_populates="progress")
