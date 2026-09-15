import os
import tempfile

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Point at a throwaway SQLite file BEFORE importing the app, since
# app.database builds its engine from settings at import time.
_tmp_db_fd, _tmp_db_path = tempfile.mkstemp(suffix=".db")
os.close(_tmp_db_fd)
os.environ["DATABASE_URL"] = f"sqlite:///{_tmp_db_path}"

from app.database import Base  # noqa: E402
from app.main import app  # noqa: E402
from app.database import get_db  # noqa: E402

test_engine = create_engine(f"sqlite:///{_tmp_db_path}", connect_args={"check_same_thread": False})
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(autouse=True)
def _setup_db():
    # Fresh schema per test (not per session) so tests are isolated from each
    # other's data — e.g. two tests both using seeded_curriculum would
    # otherwise hit UNIQUE constraint violations on the second insert.
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture(scope="session", autouse=True)
def _cleanup_db_file():
    yield
    test_engine.dispose()
    try:
        os.remove(_tmp_db_path)
    except OSError:
        pass  # best-effort; Windows may still hold a handle briefly


@pytest.fixture
def db_session():
    session = TestSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture(autouse=True)
def _override_get_db():
    def _get_test_db():
        session = TestSessionLocal()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = _get_test_db
    yield
    app.dependency_overrides.clear()


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def seeded_curriculum(db_session):
    """Seeds the alphabet track only (26 letters) + achievements. Uses the
    real asl_signs.py-backed LETTER_DESCRIPTIONS; does NOT depend on the
    verified word-signs manifest, so it's stable regardless of vocabulary
    data changes. Use seeded_vocabulary (below) for vocabulary-track tests."""
    from app.curriculum import LETTER_DESCRIPTIONS, LETTERS
    from app.models.gamification import Achievement
    from app.models.lesson import Lesson, LessonType
    from app.services.gamification_service import ACHIEVEMENT_DEFS

    for i, letter in enumerate(LETTERS, start=1):
        db_session.add(
            Lesson(
                lesson_type=LessonType.ALPHABET,
                letter=letter,
                order_index=i,
                title=f'Letter "{letter}"',
                description=LETTER_DESCRIPTIONS[letter],
            )
        )
    for code, title, description, icon in ACHIEVEMENT_DEFS:
        db_session.add(Achievement(code=code, title=title, description=description, icon=icon))
    db_session.commit()


@pytest.fixture
def seeded_vocabulary(db_session):
    """Seeds the vocabulary track only (real categories from curriculum.py,
    backed by the real verified word-signs manifest). Depends on
    ml/word_signs_verified.json actually being present and covering every
    word curriculum.py's categories reference (get_vocabulary_categories()
    asserts this itself). Does NOT seed achievements — always used alongside
    seeded_curriculum in tests, which already does that; seeding them twice
    in the same test would violate the unique constraint on Achievement.code."""
    from app.curriculum import get_vocabulary_categories
    from app.models.lesson import Lesson, LessonType

    for i, category in enumerate(get_vocabulary_categories(), start=1):
        db_session.add(
            Lesson(
                lesson_type=LessonType.VOCABULARY,
                concept_key=category["key"],
                order_index=i,
                title=category["title"],
                description=category["description"],
            )
        )
    db_session.commit()
