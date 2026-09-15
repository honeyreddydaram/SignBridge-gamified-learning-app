"""
Idempotent seed script: populates the 26-letter lesson curriculum and the
static achievement catalog. Safe to run repeatedly.

Usage (from backend/):
    python -m app.seed
"""

from app.curriculum import LETTER_DESCRIPTIONS, LETTERS
from app.database import SessionLocal
from app.models.gamification import Achievement
from app.models.lesson import Lesson
from app.services.gamification_service import ACHIEVEMENT_DEFS


def seed() -> None:
    db = SessionLocal()
    try:
        existing_letters = {l.letter for l in db.query(Lesson).all()}
        for i, letter in enumerate(LETTERS, start=1):
            if letter in existing_letters:
                continue
            db.add(
                Lesson(
                    letter=letter,
                    order_index=i,
                    title=f'Letter "{letter}"',
                    description=LETTER_DESCRIPTIONS[letter],
                )
            )
        db.commit()

        existing_codes = {a.code for a in db.query(Achievement).all()}
        for code, title, description, icon in ACHIEVEMENT_DEFS:
            if code in existing_codes:
                continue
            db.add(Achievement(code=code, title=title, description=description, icon=icon))
        db.commit()

        print(f"Seeded {len(LETTERS)} lessons and {len(ACHIEVEMENT_DEFS)} achievements (idempotent).")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
