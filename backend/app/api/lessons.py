from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.config import get_settings
from app.curriculum import LETTERS, generate_lesson_exercises, generate_vocabulary_exercises, get_vocabulary_categories
from app.database import get_db
from app.models.lesson import Lesson, LessonStatus, LessonType, UserLessonProgress
from app.models.mastery import UserSignMastery
from app.models.user import User
from app.schemas.lesson import LessonCompletionRequest, LessonCompletionResult, LessonOut
from app.services.gamification_service import (
    award_xp,
    check_and_grant_achievements,
    touch_daily_streak,
)

router = APIRouter(prefix="/api/lessons", tags=["lessons"])
settings = get_settings()


def _get_or_create_progress(db: Session, user: User, lesson: Lesson) -> UserLessonProgress:
    progress = (
        db.query(UserLessonProgress)
        .filter(UserLessonProgress.user_id == user.id, UserLessonProgress.lesson_id == lesson.id)
        .first()
    )
    if progress is None:
        is_first = lesson.order_index == 1
        progress = UserLessonProgress(
            user_id=user.id,
            lesson_id=lesson.id,
            status=LessonStatus.UNLOCKED if is_first else LessonStatus.LOCKED,
        )
        db.add(progress)
        db.flush()
    return progress


@router.get("", response_model=list[LessonOut])
def list_lessons(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    lessons = db.query(Lesson).order_by(Lesson.order_index).all()
    out = []
    for lesson in lessons:
        progress = _get_or_create_progress(db, current_user, lesson)
        out.append(_to_lesson_out(lesson, progress))
    db.commit()
    return out


def _to_lesson_out(lesson: Lesson, progress: UserLessonProgress) -> LessonOut:
    return LessonOut(
        id=lesson.id,
        lesson_type=lesson.lesson_type,
        letter=lesson.letter,
        concept_key=lesson.concept_key,
        order_index=lesson.order_index,
        title=lesson.title,
        description=lesson.description,
        status=progress.status,
        best_score_pct=progress.best_score_pct,
        attempts=progress.attempts,
        completed_at=progress.completed_at,
    )


@router.get("/{lesson_id}/exercises")
def get_lesson_exercises(
    lesson_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    lesson = db.query(Lesson).filter(Lesson.id == lesson_id).first()
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")

    progress = _get_or_create_progress(db, current_user, lesson)
    if progress.status == LessonStatus.LOCKED:
        raise HTTPException(status_code=403, detail="Lesson is locked")
    db.commit()

    if lesson.lesson_type == LessonType.ALPHABET:
        exercises = generate_lesson_exercises(lesson.letter, LETTERS)
    else:
        category = next(c for c in get_vocabulary_categories() if c["key"] == lesson.concept_key)
        mastery_rows = (
            db.query(UserSignMastery)
            .filter(UserSignMastery.user_id == current_user.id, UserSignMastery.word.in_(category["words"]))
            .all()
        )
        mastery_by_word = {m.word: m.state.value for m in mastery_rows}
        exercises = generate_vocabulary_exercises(lesson.concept_key, mastery_by_word)

    return {
        "lesson": _to_lesson_out(lesson, progress),
        "exercises": exercises,
    }


@router.post("/{lesson_id}/complete", response_model=LessonCompletionResult)
def complete_lesson(
    lesson_id: int,
    payload: LessonCompletionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    lesson = db.query(Lesson).filter(Lesson.id == lesson_id).first()
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")

    progress = _get_or_create_progress(db, current_user, lesson)
    if progress.status == LessonStatus.LOCKED:
        raise HTTPException(status_code=403, detail="Lesson is locked")

    if payload.total_count <= 0:
        raise HTTPException(status_code=400, detail="total_count must be positive")
    if payload.correct_count < 0 or payload.correct_count > payload.total_count:
        raise HTTPException(status_code=400, detail="correct_count out of range")

    from datetime import datetime, timezone

    score_pct = round(100 * payload.correct_count / payload.total_count)
    progress.attempts += 1
    progress.best_score_pct = max(progress.best_score_pct, score_pct)
    first_completion = progress.status != LessonStatus.COMPLETED
    progress.status = LessonStatus.COMPLETED
    progress.completed_at = datetime.now(timezone.utc)

    xp_awarded = 0
    leveled_up = False
    lesson_key = lesson.letter or lesson.concept_key
    if first_completion:
        xp_awarded += settings.xp_per_lesson_complete
        if score_pct == 100:
            xp_awarded += settings.xp_per_perfect_lesson
        leveled_up = award_xp(db, current_user, xp_awarded, reason=f"lesson_complete:{lesson_key}")

    touch_daily_streak(db, current_user)

    newly_unlocked_ids: list[int] = []
    if first_completion:
        # Scoped to the same track (alphabet vs vocabulary): the two tracks
        # unlock independently, so completing the last alphabet lesson must
        # not unlock the first vocabulary lesson or vice versa.
        next_lesson = (
            db.query(Lesson)
            .filter(Lesson.lesson_type == lesson.lesson_type, Lesson.order_index == lesson.order_index + 1)
            .first()
        )
        if next_lesson:
            next_progress = _get_or_create_progress(db, current_user, next_lesson)
            if next_progress.status == LessonStatus.LOCKED:
                next_progress.status = LessonStatus.UNLOCKED
                newly_unlocked_ids.append(next_lesson.id)

    db.flush()  # autoflush is off; achievement checks query committed-shape state via pending rows
    new_achievements = check_and_grant_achievements(db, current_user)

    db.commit()
    db.refresh(progress)
    db.refresh(current_user)

    return LessonCompletionResult(
        lesson=_to_lesson_out(lesson, progress),
        xp_awarded=xp_awarded,
        newly_unlocked_lesson_ids=newly_unlocked_ids,
        new_achievements=new_achievements,
        leveled_up=leveled_up,
        level=current_user.level,
        xp_total=current_user.xp_total,
    )
