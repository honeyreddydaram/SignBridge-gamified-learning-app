import json
from functools import lru_cache
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.config import get_settings
from app.database import get_db
from app.models.practice import PracticeAttempt
from app.models.user import User
from app.schemas.recognition import RecognitionRequest, RecognitionResult
from app.services.gamification_service import (
    award_xp,
    check_and_grant_achievements,
    lose_heart,
    regenerate_hearts,
    touch_daily_streak,
)
from app.services.recognition_service import get_recognition_service

router = APIRouter(prefix="/api/recognition", tags=["recognition"])
settings = get_settings()


@router.get("/status")
def recognition_status():
    service = get_recognition_service()
    return {"ready": service.is_ready, "error": service.load_error}


@lru_cache
def _load_reference_landmarks() -> dict:
    path = Path(settings.recognition_model_path).parent / "reference_landmarks.json"
    if not path.exists():
        return {}
    return json.loads(path.read_text())


@router.get("/reference-signs")
def reference_signs():
    """
    Per-letter representative hand-landmark pose, computed from real training
    data by ml/scripts/train.py (compute_reference_landmarks). Used by the
    frontend to render sign cards and the fingerspelling animation as SVG
    hand-skeletons — real derived data, not stock images (whose license
    doesn't permit redistribution) and not fabricated illustrations.
    """
    refs = _load_reference_landmarks()
    if not refs:
        raise HTTPException(status_code=503, detail="Reference landmarks not available — run ml training pipeline.")
    return refs


@router.post("/predict", response_model=RecognitionResult)
def predict(
    payload: RecognitionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = get_recognition_service()
    if not service.is_ready:
        raise HTTPException(
            status_code=503,
            detail=f"Recognition model not available: {service.load_error}",
        )

    try:
        rgb = service.decode_base64_image(payload.image_base64)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    hand_detected, letter, confidence = service.predict(rgb)
    is_confident = hand_detected and confidence >= settings.recognition_confidence_threshold
    predicted_letter = letter if is_confident else None

    correct: bool | None = None
    is_challenge = payload.target_letter is not None
    if is_challenge and is_confident:
        correct = predicted_letter == payload.target_letter.upper()

    # Only log a persisted attempt for directed challenges with a confident
    # read, to avoid flooding the table with every idle webcam frame.
    if is_challenge and is_confident:
        regenerate_hearts(db, current_user)
        db.add(
            PracticeAttempt(
                user_id=current_user.id,
                lesson_id=payload.lesson_id,
                target_letter=payload.target_letter.upper(),
                predicted_letter=predicted_letter,
                confidence=confidence,
                is_correct=correct,
            )
        )
        if correct:
            award_xp(db, current_user, settings.xp_per_correct_answer, reason="camera_challenge_correct")
            touch_daily_streak(db, current_user)
            check_and_grant_achievements(db, current_user)
        else:
            lose_heart(db, current_user)
        db.commit()

    return RecognitionResult(
        hand_detected=hand_detected,
        predicted_letter=predicted_letter,
        confidence=round(confidence, 4),
        is_confident=is_confident,
        correct=correct,
    )
