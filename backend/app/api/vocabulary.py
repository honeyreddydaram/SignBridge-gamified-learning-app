from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.asl_signs import SUPPORTED_SIGNS, normalize_word
from app.database import get_db
from app.models.user import User
from app.schemas.mastery import MasterySummary, SignInteractionRequest, SignInteractionResult
from app.services.gamification_service import check_and_grant_achievements, touch_daily_streak
from app.services.mastery_service import mastery_summary, needs_practice, record_sign_interaction

router = APIRouter(prefix="/api/vocabulary", tags=["vocabulary"])

VALID_INTERACTION_TYPES = {"viewed", "recognize", "produce_selfcheck", "recall_selfcheck"}


@router.post("/interaction", response_model=SignInteractionResult)
def record_interaction(
    payload: SignInteractionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Records one Learn/Recognize/Produce/Recall interaction and updates the
    word's mastery state. "recognize" is objectively graded (a real MCQ
    answer); "produce_selfcheck" and "recall_selfcheck" are the LEARNER'S
    OWN self-report — the trained recognition model cannot validate dynamic
    word-level signs (see mastery_service.py), so these are honest
    self-assessment, not model-verified accuracy, and are worth less XP.
    """
    word = normalize_word(payload.word)
    if word not in SUPPORTED_SIGNS:
        raise HTTPException(status_code=404, detail=f"'{payload.word}' is not a supported vocabulary word")
    if payload.interaction_type not in VALID_INTERACTION_TYPES:
        raise HTTPException(status_code=400, detail=f"invalid interaction_type: {payload.interaction_type}")
    if payload.interaction_type == "recognize" and payload.correct is None:
        raise HTTPException(status_code=400, detail="'correct' is required for interaction_type 'recognize'")

    mastery, just_mastered, xp_awarded = record_sign_interaction(
        db, current_user, word, payload.interaction_type, payload.correct
    )

    if xp_awarded > 0:
        touch_daily_streak(db, current_user)

    db.flush()
    new_achievements = check_and_grant_achievements(db, current_user)

    db.commit()
    db.refresh(mastery)
    db.refresh(current_user)

    return SignInteractionResult(
        word=word,
        state=mastery.state.value,
        just_mastered=just_mastered,
        xp_awarded=xp_awarded,
        new_achievements=new_achievements,
        level=current_user.level,
        xp_total=current_user.xp_total,
    )


@router.get("/mastery-summary", response_model=MasterySummary)
def get_mastery_summary(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    counts = mastery_summary(db, current_user)
    practice_list = needs_practice(db, current_user)
    return MasterySummary(
        new=counts["new"],
        learning=counts["learning"],
        practicing=counts["practicing"],
        mastered=counts["mastered"],
        needs_practice=practice_list,
    )
