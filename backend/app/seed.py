"""
Idempotent seed script: populates both lesson tracks (26-letter alphabet +
vocabulary categories built from the verified 114-word sign manifest) and
the static achievement catalog. Safe to run repeatedly.

Usage (from backend/):
    python -m app.seed
"""

from app.curriculum import LETTER_DESCRIPTIONS, LETTERS, get_vocabulary_categories
from app.database import SessionLocal
from app.models.gamification import Achievement
from app.models.lesson import Lesson, LessonType
from app.services.gamification_service import ACHIEVEMENT_DEFS


def seed() -> None:
    db = SessionLocal()
    try:
        existing_letters = {l.letter for l in db.query(Lesson).filter(Lesson.lesson_type == LessonType.ALPHABET)}
        for i, letter in enumerate(LETTERS, start=1):
            if letter in existing_letters:
                continue
            db.add(
                Lesson(
                    lesson_type=LessonType.ALPHABET,
                    letter=letter,
                    order_index=i,
                    title=f'Letter "{letter}"',
                    description=LETTER_DESCRIPTIONS[letter],
                )
            )
        db.commit()

        existing_keys = {
            l.concept_key for l in db.query(Lesson).filter(Lesson.lesson_type == LessonType.VOCABULARY)
        }
        for i, category in enumerate(get_vocabulary_categories(), start=1):
            if category["key"] in existing_keys:
                continue
            db.add(
                Lesson(
                    lesson_type=LessonType.VOCABULARY,
                    concept_key=category["key"],
                    order_index=i,
                    title=category["title"],
                    description=category["description"],
                )
            )
        db.commit()

        existing_codes = {a.code for a in db.query(Achievement).all()}
        for code, title, description, icon in ACHIEVEMENT_DEFS:
            if code in existing_codes:
                continue
            db.add(Achievement(code=code, title=title, description=description, icon=icon))
        db.commit()

        vocab_count = len(get_vocabulary_categories())
        print(
            f"Seeded {len(LETTERS)} alphabet lessons, {vocab_count} vocabulary lessons, "
            f"and {len(ACHIEVEMENT_DEFS)} achievements (idempotent)."
        )
    finally:
        db.close()


if __name__ == "__main__":
    seed()
