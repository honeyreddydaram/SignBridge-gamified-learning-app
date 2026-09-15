"""
Centralizes XP, leveling, streaks, hearts and achievement logic so lesson
completion and camera-challenge endpoints don't duplicate this bookkeeping.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.config import get_settings
from app.models.gamification import Achievement, UserAchievement, XPTransaction
from app.models.lesson import LessonStatus, UserLessonProgress
from app.models.user import User

settings = get_settings()

# XP required to reach level N = 100 * N (level 1 -> 2 needs 100 XP, 2 -> 3 needs 200 more, etc.)
def _level_for_xp(xp_total: int) -> int:
    level = 1
    remaining = xp_total
    threshold = 100
    while remaining >= threshold:
        remaining -= threshold
        level += 1
        threshold = 100 * level
    return level


def award_xp(db: Session, user: User, amount: int, reason: str) -> bool:
    """Returns True if this award caused a level-up."""
    if amount <= 0:
        return False
    db.add(XPTransaction(user_id=user.id, amount=amount, reason=reason))
    old_level = user.level
    user.xp_total += amount
    user.level = _level_for_xp(user.xp_total)
    return user.level > old_level


def touch_daily_streak(db: Session, user: User) -> None:
    """Call once per day the user does *any* graded activity."""
    today = datetime.now(timezone.utc).date()
    if user.last_activity_date == today:
        return  # already counted today

    if user.last_activity_date == today - timedelta(days=1):
        user.current_streak += 1
    else:
        user.current_streak = 1  # streak broken or first-ever activity

    user.longest_streak = max(user.longest_streak, user.current_streak)
    user.last_activity_date = today


def regenerate_hearts(db: Session, user: User) -> None:
    """Hearts refill one at a time every `heart_regen_minutes`, capped at max."""
    if user.hearts >= settings.max_hearts:
        user.hearts_last_refill_at = datetime.now(timezone.utc)
        return

    now = datetime.now(timezone.utc)
    last = user.hearts_last_refill_at
    if last.tzinfo is None:
        last = last.replace(tzinfo=timezone.utc)

    elapsed_minutes = (now - last).total_seconds() / 60
    regen_count = int(elapsed_minutes // settings.heart_regen_minutes)
    if regen_count <= 0:
        return

    user.hearts = min(settings.max_hearts, user.hearts + regen_count)
    user.hearts_last_refill_at = last + timedelta(minutes=regen_count * settings.heart_regen_minutes)


def lose_heart(db: Session, user: User) -> None:
    if user.hearts > 0:
        user.hearts -= 1
        if user.hearts == settings.max_hearts - 1:
            user.hearts_last_refill_at = datetime.now(timezone.utc)


ACHIEVEMENT_DEFS = [
    ("first_lesson", "First Steps", "Complete your first lesson.", "\U0001F476"),
    ("alphabet_complete", "Alphabet Master", "Complete all 26 letter lessons.", "\U0001F3C6"),
    ("streak_3", "On a Roll", "Reach a 3-day streak.", "\U0001F525"),
    ("streak_7", "Week Warrior", "Reach a 7-day streak.", "\U0001F4AA"),
    ("perfect_lesson", "Perfectionist", "Complete a lesson with a perfect score.", "\U0001F31F"),
    ("camera_pro", "Camera Pro", "Get 25 correct camera recognition challenges.", "\U0001F4F7"),
]


def check_and_grant_achievements(db: Session, user: User) -> list[str]:
    """Returns titles of newly granted achievements."""
    existing_codes = {
        ua.achievement.code for ua in user.achievements
    }
    newly_granted: list[str] = []

    completed_lessons = (
        db.query(UserLessonProgress)
        .filter(UserLessonProgress.user_id == user.id, UserLessonProgress.status == LessonStatus.COMPLETED)
        .count()
    )
    perfect_lessons = (
        db.query(UserLessonProgress)
        .filter(
            UserLessonProgress.user_id == user.id,
            UserLessonProgress.status == LessonStatus.COMPLETED,
            UserLessonProgress.best_score_pct == 100,
        )
        .count()
    )

    to_check = []
    if completed_lessons >= 1:
        to_check.append("first_lesson")
    if completed_lessons >= 26:
        to_check.append("alphabet_complete")
    if user.current_streak >= 3:
        to_check.append("streak_3")
    if user.current_streak >= 7:
        to_check.append("streak_7")
    if perfect_lessons >= 1:
        to_check.append("perfect_lesson")

    for code in to_check:
        if code in existing_codes:
            continue
        achievement = db.query(Achievement).filter(Achievement.code == code).first()
        if not achievement:
            continue
        db.add(UserAchievement(user_id=user.id, achievement_id=achievement.id))
        newly_granted.append(achievement.title)
        existing_codes.add(code)

    return newly_granted
