"""Quest progress bookkeeping — reads/writes UserQuestProgress against the
static Quest catalog seeded from app.quests.QUEST_DEFS."""

from __future__ import annotations

import json
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.config import get_settings
from app.models.mastery import Quest, UserQuestProgress
from app.models.user import User
from app.services.gamification_service import award_xp

settings = get_settings()


def get_or_create_progress(db: Session, user: User, quest: Quest) -> UserQuestProgress:
    progress = (
        db.query(UserQuestProgress)
        .filter(UserQuestProgress.user_id == user.id, UserQuestProgress.quest_id == quest.id)
        .first()
    )
    if progress is None:
        progress = UserQuestProgress(user_id=user.id, quest_id=quest.id)
        db.add(progress)
        db.flush()
    return progress


def completed_words(progress: UserQuestProgress) -> list[str]:
    return json.loads(progress.completed_words_json)


def record_quest_step(
    db: Session, user: User, quest: Quest, word: str, self_correct: bool
) -> tuple[UserQuestProgress, int, bool]:
    """
    Records a self-checked attempt at one word within a quest. Returns
    (progress, xp_awarded, quest_just_completed).

    Only a correct self-check advances the checklist — an honest "I need
    more practice" doesn't mark that word done, so a quest can't be
    steamrolled by clicking through regardless of the self-report.

    NOTE: per-word self-check XP is NOT awarded here — the caller
    (api/quests.py) also records this as a recall_selfcheck mastery
    interaction, which already awards xp_per_selfcheck. Awarding it in both
    places would double-count. This function only awards the one-time
    quest-completion bonus.
    """
    word = word.upper()
    quest_words = json.loads(quest.words_json)
    if word not in quest_words:
        raise ValueError(f"'{word}' is not part of quest '{quest.quest_key}'")

    progress = get_or_create_progress(db, user, quest)
    done = set(completed_words(progress))
    xp_awarded = 0

    if self_correct and word not in done:
        done.add(word)
        progress.completed_words_json = json.dumps(sorted(done))

    quest_just_completed = False
    if done >= set(quest_words) and progress.status != "completed":
        progress.status = "completed"
        progress.completed_at = datetime.now(timezone.utc)
        quest_just_completed = True
        xp_awarded += settings.xp_per_quest_complete

    if xp_awarded > 0:
        award_xp(db, user, xp_awarded, reason=f"quest_step:{quest.quest_key}:{word}")

    return progress, xp_awarded, quest_just_completed
