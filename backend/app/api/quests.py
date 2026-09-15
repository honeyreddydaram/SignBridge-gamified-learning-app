import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.asl_signs import normalize_word
from app.database import get_db
from app.models.mastery import MasteryState, Quest, UserSignMastery
from app.models.user import User
from app.schemas.quest import QuestOut, QuestStepRequest, QuestStepResult, QuestWordStatus
from app.services.gamification_service import check_and_grant_achievements, touch_daily_streak
from app.services.mastery_service import get_or_create_mastery, record_sign_interaction
from app.services.quest_service import completed_words, get_or_create_progress, record_quest_step

router = APIRouter(prefix="/api/quests", tags=["quests"])


def _to_quest_out(db: Session, user: User, quest: Quest) -> QuestOut:
    progress = get_or_create_progress(db, user, quest)
    db.commit()
    done = set(completed_words(progress))
    words = json.loads(quest.words_json)

    word_statuses = []
    for word in words:
        mastery = (
            db.query(UserSignMastery)
            .filter(UserSignMastery.user_id == user.id, UserSignMastery.word == word)
            .first()
        )
        word_statuses.append(
            QuestWordStatus(
                word=word,
                completed=word in done,
                mastery_state=mastery.state.value if mastery else MasteryState.NEW.value,
            )
        )

    return QuestOut(
        key=quest.quest_key,
        quest_type=quest.quest_type.value,
        title=quest.title,
        description=quest.description,
        prompt=quest.prompt,
        words=word_statuses,
        status=progress.status,
        completed_at=progress.completed_at,
    )


@router.get("", response_model=list[QuestOut])
def list_quests(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    quests = db.query(Quest).order_by(Quest.order_index).all()
    return [_to_quest_out(db, current_user, q) for q in quests]


@router.get("/{quest_key}", response_model=QuestOut)
def get_quest(quest_key: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    quest = db.query(Quest).filter(Quest.quest_key == quest_key).first()
    if not quest:
        raise HTTPException(status_code=404, detail="Quest not found")
    return _to_quest_out(db, current_user, quest)


@router.post("/{quest_key}/steps", response_model=QuestStepResult)
def submit_quest_step(
    quest_key: str,
    payload: QuestStepRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Records one self-checked quest step. Like all vocabulary camera
    interactions, this is a SELF-REPORT ("I signed it correctly") — the
    trained recognition model cannot validate these dynamic word-level
    signs, so nothing here is model-graded. A quest step also feeds the
    word's mastery state as a recall_selfcheck (quests are blind-recall
    reinforcement of already-taught vocabulary, not a first teaching pass).
    """
    quest = db.query(Quest).filter(Quest.quest_key == quest_key).first()
    if not quest:
        raise HTTPException(status_code=404, detail="Quest not found")

    word = normalize_word(payload.word)
    words = json.loads(quest.words_json)
    if word not in words:
        raise HTTPException(status_code=400, detail=f"'{payload.word}' is not part of this quest")

    _, quest_xp, quest_completed = record_quest_step(db, current_user, quest, word, payload.self_correct)

    mastery_xp = 0
    if payload.self_correct:
        get_or_create_mastery(db, current_user, word)
        _, _, mastery_xp = record_sign_interaction(db, current_user, word, "recall_selfcheck")

    total_xp = quest_xp + mastery_xp
    if total_xp > 0:
        touch_daily_streak(db, current_user)

    db.flush()
    new_achievements = check_and_grant_achievements(db, current_user)
    db.commit()

    return QuestStepResult(
        quest=_to_quest_out(db, current_user, quest),
        xp_awarded=total_xp,
        quest_completed=quest_completed,
        new_achievements=new_achievements,
    )
