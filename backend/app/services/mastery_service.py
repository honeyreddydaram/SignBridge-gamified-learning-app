"""
Learn -> Recognize -> Produce -> Recall -> Master loop bookkeeping.

State machine (deliberately simple, see UserSignMastery's docstring for the
full rationale):
    NEW        -> LEARNING    on any first interaction
    LEARNING   -> PRACTICING  once recognize_correct_count >= 2
                              AND produce_selfcheck_count >= 1
    PRACTICING -> MASTERED    once a recall self-check succeeds AND the user
                              has interacted with this word on >= 2 distinct
                              calendar days (so a single sitting can't
                              mastery a word solely by clicking through it —
                              recall has to succeed on a later visit)
MASTERED is sticky — it never downgrades.

IMPORTANT ML-limitation note: "recognize_correct" comes from a real graded
multiple-choice quiz (objective). "produce_selfcheck" and "recall_selfcheck"
are the LEARNER'S OWN self-report ("I signed it correctly") — the trained
recognition model cannot validate dynamic word-level signs (see
recognition_service.py / MODEL_CARD.md), so these counts measure honest
self-assessment, not model-verified accuracy. Callers must never present
self-check results as if they were model-graded.
"""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.config import get_settings
from app.models.mastery import MasteryState, UserSignMastery
from app.models.user import User
from app.services.gamification_service import award_xp

settings = get_settings()

PRACTICING_RECOGNIZE_THRESHOLD = 2
PRACTICING_PRODUCE_THRESHOLD = 1
MASTERED_MIN_DISTINCT_DAYS = 2


def get_or_create_mastery(db: Session, user: User, word: str) -> UserSignMastery:
    word = word.upper()
    mastery = (
        db.query(UserSignMastery)
        .filter(UserSignMastery.user_id == user.id, UserSignMastery.word == word)
        .first()
    )
    if mastery is None:
        mastery = UserSignMastery(user_id=user.id, word=word)
        db.add(mastery)
        db.flush()
    return mastery


def _recompute_state(mastery: UserSignMastery) -> MasteryState:
    if mastery.state == MasteryState.MASTERED:
        return MasteryState.MASTERED

    if (
        mastery.state == MasteryState.PRACTICING
        and mastery.recall_selfcheck_count >= 1
        and mastery.distinct_days_interacted >= MASTERED_MIN_DISTINCT_DAYS
    ):
        return MasteryState.MASTERED

    if (
        mastery.recognize_correct_count >= PRACTICING_RECOGNIZE_THRESHOLD
        and mastery.produce_selfcheck_count >= PRACTICING_PRODUCE_THRESHOLD
    ):
        return MasteryState.PRACTICING

    return MasteryState.LEARNING


InteractionType = str  # "viewed" | "recognize" | "produce_selfcheck" | "recall_selfcheck"


def record_sign_interaction(
    db: Session,
    user: User,
    word: str,
    interaction_type: InteractionType,
    correct: bool | None = None,
) -> tuple[UserSignMastery, bool, int]:
    """
    Records one interaction and recomputes mastery state.
    Returns (mastery, just_mastered, xp_awarded).
    """
    mastery = get_or_create_mastery(db, user, word)

    today = datetime.now(timezone.utc).date()
    if mastery.last_interaction_date != today:
        mastery.distinct_days_interacted += 1
        mastery.last_interaction_date = today

    xp_awarded = 0
    if interaction_type == "recognize":
        mastery.recognize_attempt_count += 1
        if correct:
            mastery.recognize_correct_count += 1
            xp_awarded += settings.xp_per_correct_answer
    elif interaction_type == "produce_selfcheck":
        mastery.produce_selfcheck_count += 1
        xp_awarded += settings.xp_per_selfcheck
    elif interaction_type == "recall_selfcheck":
        mastery.recall_selfcheck_count += 1
        xp_awarded += settings.xp_per_selfcheck
    elif interaction_type == "viewed":
        pass  # just touches distinct_days_interacted above
    else:
        raise ValueError(f"unknown interaction_type: {interaction_type}")

    old_state = mastery.state
    new_state = _recompute_state(mastery)
    just_mastered = new_state == MasteryState.MASTERED and old_state != MasteryState.MASTERED
    mastery.state = new_state
    if just_mastered:
        mastery.mastered_at = datetime.now(timezone.utc)
        xp_awarded += settings.xp_per_sign_mastered

    if xp_awarded > 0:
        award_xp(db, user, xp_awarded, reason=f"sign_interaction:{word}:{interaction_type}")

    return mastery, just_mastered, xp_awarded


def mastery_summary(db: Session, user: User, words: list[str] | None = None) -> dict:
    """Counts by state, optionally restricted to a given word list (e.g. one
    quest's words). Words with no mastery row yet count as 'new'."""
    query = db.query(UserSignMastery).filter(UserSignMastery.user_id == user.id)
    rows = {m.word: m for m in query.all()}

    counts = {"new": 0, "learning": 0, "practicing": 0, "mastered": 0}
    universe = [w.upper() for w in words] if words is not None else list(rows.keys())
    # If restricted to a word list, words with no row are "new"; if
    # unrestricted, only words with an actual row are counted (a user with
    # no interactions yet has no rows at all, and "new" would otherwise be
    # unbounded against the full 114-word manifest, which isn't meaningful
    # as a per-user count without a reference word list).
    if words is not None:
        for w in universe:
            state = rows[w].state.value if w in rows else "new"
            counts[state] += 1
    else:
        for m in rows.values():
            counts[m.state.value] += 1

    return counts


def needs_practice(db: Session, user: User, limit: int = 10) -> list[str]:
    """Words in LEARNING or PRACTICING state — actively being worked on but
    not yet mastered — most-recently-touched first."""
    rows = (
        db.query(UserSignMastery)
        .filter(
            UserSignMastery.user_id == user.id,
            UserSignMastery.state.in_([MasteryState.LEARNING, MasteryState.PRACTICING]),
        )
        .order_by(UserSignMastery.updated_at.desc())
        .limit(limit)
        .all()
    )
    return [r.word for r in rows]
