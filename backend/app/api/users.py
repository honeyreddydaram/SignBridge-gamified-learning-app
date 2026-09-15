from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.database import get_db
from app.models.gamification import UserAchievement
from app.models.user import User
from app.schemas.user import UserProfile
from app.services.gamification_service import regenerate_hearts

router = APIRouter(prefix="/api/users", tags=["users"])


@router.get("/me", response_model=UserProfile)
def get_me(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    regenerate_hearts(db, current_user)
    db.commit()
    db.refresh(current_user)
    return current_user


@router.get("/me/achievements")
def get_my_achievements(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    rows = (
        db.query(UserAchievement)
        .filter(UserAchievement.user_id == current_user.id)
        .all()
    )
    return [
        {
            "code": ua.achievement.code,
            "title": ua.achievement.title,
            "description": ua.achievement.description,
            "icon": ua.achievement.icon,
            "earned_at": ua.earned_at,
        }
        for ua in rows
    ]
