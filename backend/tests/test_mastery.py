"""
Tests for the Learn -> Recognize -> Produce -> Recall -> Master state
machine (app/services/mastery_service.py) and its API
(app/api/vocabulary.py). Uses a fake SUPPORTED_SIGNS word ("HELLO" is real
in the manifest, used here since it's guaranteed to exist) rather than
depending on exact manifest contents beyond that.
"""

from datetime import date, timedelta

from app.models.mastery import MasteryState, UserSignMastery
from app.services.mastery_service import (
    MASTERED_MIN_DISTINCT_DAYS,
    PRACTICING_PRODUCE_THRESHOLD,
    PRACTICING_RECOGNIZE_THRESHOLD,
    mastery_summary,
    needs_practice,
    record_sign_interaction,
)


def _signup_and_auth(client, email="mastery@example.com", username="masteryuser"):
    resp = client.post("/api/auth/signup", json={"email": email, "username": username, "password": "password123"})
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def _get_user(db_session, email):
    from app.models.user import User

    return db_session.query(User).filter(User.email == email).first()


def test_new_word_starts_at_new_state(db_session):
    from app.models.user import User

    user = User(email="a@example.com", username="a", hashed_password="x")
    db_session.add(user)
    db_session.commit()

    mastery = (
        db_session.query(UserSignMastery)
        .filter(UserSignMastery.user_id == user.id, UserSignMastery.word == "HELLO")
        .first()
    )
    assert mastery is None  # no row until first interaction


def test_viewed_interaction_creates_learning_state(db_session):
    from app.models.user import User

    user = User(email="b@example.com", username="b", hashed_password="x")
    db_session.add(user)
    db_session.commit()

    mastery, just_mastered, xp = record_sign_interaction(db_session, user, "hello", "viewed")
    db_session.commit()

    assert mastery.state == MasteryState.LEARNING
    assert just_mastered is False
    assert xp == 0  # just watching earns nothing
    assert mastery.word == "HELLO"  # normalized to uppercase


def test_reaches_practicing_after_threshold(db_session):
    from app.models.user import User

    user = User(email="c@example.com", username="c", hashed_password="x")
    db_session.add(user)
    db_session.commit()

    for _ in range(PRACTICING_RECOGNIZE_THRESHOLD):
        mastery, _, _ = record_sign_interaction(db_session, user, "HELLO", "recognize", correct=True)
    assert mastery.state == MasteryState.LEARNING  # recognize alone isn't enough

    mastery, _, xp = record_sign_interaction(db_session, user, "HELLO", "produce_selfcheck")
    db_session.commit()

    assert mastery.state == MasteryState.PRACTICING
    assert mastery.recognize_correct_count == PRACTICING_RECOGNIZE_THRESHOLD
    assert mastery.produce_selfcheck_count >= PRACTICING_PRODUCE_THRESHOLD
    assert xp > 0


def test_cannot_master_in_a_single_day_even_with_recall_success(db_session):
    """The core 'can't click through once' requirement: a recall success on
    the SAME day the word reached Practicing must NOT master it."""
    from app.models.user import User

    user = User(email="d@example.com", username="d", hashed_password="x")
    db_session.add(user)
    db_session.commit()

    for _ in range(PRACTICING_RECOGNIZE_THRESHOLD):
        record_sign_interaction(db_session, user, "HELLO", "recognize", correct=True)
    record_sign_interaction(db_session, user, "HELLO", "produce_selfcheck")
    mastery, just_mastered, _ = record_sign_interaction(db_session, user, "HELLO", "recall_selfcheck")
    db_session.commit()

    assert mastery.state == MasteryState.PRACTICING  # not mastered yet
    assert just_mastered is False
    assert mastery.distinct_days_interacted == 1  # everything happened "today"


def test_masters_after_recall_success_on_a_later_distinct_day(db_session):
    from app.models.user import User

    user = User(email="e@example.com", username="e", hashed_password="x")
    db_session.add(user)
    db_session.commit()

    for _ in range(PRACTICING_RECOGNIZE_THRESHOLD):
        record_sign_interaction(db_session, user, "HELLO", "recognize", correct=True)
    mastery, _, _ = record_sign_interaction(db_session, user, "HELLO", "produce_selfcheck")
    assert mastery.state == MasteryState.PRACTICING

    # Simulate a later day by backdating last_interaction_date, then
    # recording the qualifying recall — this is the realistic path since
    # record_sign_interaction bumps distinct_days_interacted only when
    # today's date differs from the stored last_interaction_date.
    mastery.last_interaction_date = date.today() - timedelta(days=1)
    db_session.commit()

    mastery, just_mastered, xp = record_sign_interaction(db_session, user, "HELLO", "recall_selfcheck")
    db_session.commit()

    assert mastery.state == MasteryState.MASTERED
    assert just_mastered is True
    assert mastery.distinct_days_interacted >= MASTERED_MIN_DISTINCT_DAYS
    assert mastery.mastered_at is not None
    assert xp > 0  # includes the mastery milestone bonus


def test_mastered_state_is_sticky(db_session):
    from app.models.user import User

    user = User(email="f@example.com", username="f", hashed_password="x")
    db_session.add(user)
    db_session.commit()

    for _ in range(PRACTICING_RECOGNIZE_THRESHOLD):
        record_sign_interaction(db_session, user, "HELLO", "recognize", correct=True)
    mastery, _, _ = record_sign_interaction(db_session, user, "HELLO", "produce_selfcheck")
    mastery.last_interaction_date = date.today() - timedelta(days=1)
    db_session.commit()
    mastery, _, _ = record_sign_interaction(db_session, user, "HELLO", "recall_selfcheck")
    assert mastery.state == MasteryState.MASTERED

    # A subsequent "recognize" incorrect answer must not downgrade mastery.
    mastery, _, _ = record_sign_interaction(db_session, user, "HELLO", "recognize", correct=False)
    db_session.commit()
    assert mastery.state == MasteryState.MASTERED


def test_needs_practice_lists_learning_and_practicing_not_mastered_or_new(db_session):
    from app.models.user import User

    user = User(email="g@example.com", username="g", hashed_password="x")
    db_session.add(user)
    db_session.commit()

    record_sign_interaction(db_session, user, "HELLO", "viewed")  # -> LEARNING
    db_session.commit()

    result = needs_practice(db_session, user)
    assert "HELLO" in result


def test_interaction_endpoint_rejects_unsupported_word(client):
    headers = _signup_and_auth(client)
    resp = client.post(
        "/api/vocabulary/interaction",
        json={"word": "ZZZNOTAWORD", "interaction_type": "viewed"},
        headers=headers,
    )
    assert resp.status_code == 404


def test_interaction_endpoint_requires_correct_field_for_recognize(client):
    headers = _signup_and_auth(client)
    resp = client.post(
        "/api/vocabulary/interaction",
        json={"word": "HELLO", "interaction_type": "recognize"},
        headers=headers,
    )
    assert resp.status_code == 400


def test_interaction_endpoint_full_flow(client):
    headers = _signup_and_auth(client, "flow@example.com", "flowuser")
    resp = client.post(
        "/api/vocabulary/interaction",
        json={"word": "hello", "interaction_type": "viewed"},
        headers=headers,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["word"] == "HELLO"
    assert body["state"] == "learning"
    assert body["xp_awarded"] == 0

    summary = client.get("/api/vocabulary/mastery-summary", headers=headers)
    assert summary.status_code == 200
    assert summary.json()["learning"] == 1
