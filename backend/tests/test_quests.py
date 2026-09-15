"""Tests for Sign Quests (app/api/quests.py, app/services/quest_service.py).
Seeds real quest data (app.quests.QUEST_DEFS) against a fresh test DB —
mirrors the actual seed.py flow rather than a fake fixture, since the quest
catalog is small, static data that's part of what's being tested."""

import json

import pytest

from app.models.mastery import Quest


def _signup_and_auth(client, email="quest@example.com", username="questuser"):
    resp = client.post("/api/auth/signup", json={"email": email, "username": username, "password": "password123"})
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def seeded_quests(db_session):
    from app.quests import get_quest_defs

    for i, quest in enumerate(get_quest_defs(), start=1):
        db_session.add(
            Quest(
                quest_key=quest["key"],
                quest_type=quest["type"],
                title=quest["title"],
                description=quest["description"],
                prompt=quest.get("prompt"),
                words_json=json.dumps(quest["words"]),
                order_index=i,
            )
        )
    db_session.commit()


def test_list_quests_includes_greetings_quest(client, seeded_quests):
    headers = _signup_and_auth(client)
    resp = client.get("/api/quests", headers=headers)
    assert resp.status_code == 200
    quests = resp.json()
    keys = [q["key"] for q in quests]
    assert "greetings_quest" in keys

    greetings = next(q for q in quests if q["key"] == "greetings_quest")
    assert greetings["quest_type"] == "mission"
    assert [w["word"] for w in greetings["words"]] == ["HELLO", "PLEASE", "THANKYOU"]
    assert all(w["completed"] is False for w in greetings["words"])
    assert greetings["status"] == "in_progress"


def test_scenario_quest_has_prompt(client, seeded_quests):
    headers = _signup_and_auth(client, "s@example.com", "scenariouser")
    resp = client.get("/api/quests/meet_someone_scenario", headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["quest_type"] == "scenario"
    assert "greet" in body["prompt"].lower()
    assert body["words"] == [{"word": "HELLO", "completed": False, "mastery_state": "new"}]


def test_incorrect_self_check_does_not_complete_word(client, seeded_quests):
    headers = _signup_and_auth(client, "i@example.com", "incorrectuser")
    resp = client.post(
        "/api/quests/greetings_quest/steps", json={"word": "HELLO", "self_correct": False}, headers=headers
    )
    assert resp.status_code == 200
    body = resp.json()
    hello_status = next(w for w in body["quest"]["words"] if w["word"] == "HELLO")
    assert hello_status["completed"] is False
    assert body["xp_awarded"] == 0
    assert body["quest_completed"] is False


def test_correct_self_check_completes_word_and_feeds_mastery(client, seeded_quests):
    headers = _signup_and_auth(client, "j@example.com", "correctuser")
    resp = client.post(
        "/api/quests/greetings_quest/steps", json={"word": "HELLO", "self_correct": True}, headers=headers
    )
    assert resp.status_code == 200
    body = resp.json()
    hello_status = next(w for w in body["quest"]["words"] if w["word"] == "HELLO")
    assert hello_status["completed"] is True
    assert hello_status["mastery_state"] in ("learning", "practicing")  # recall_selfcheck was recorded
    assert body["xp_awarded"] > 0
    assert body["quest_completed"] is False  # PLEASE, THANKYOU still pending


def test_completing_all_quest_words_completes_the_quest(client, seeded_quests, seeded_curriculum):
    # seeded_curriculum (not otherwise needed here) is what seeds the
    # Achievement catalog — check_and_grant_achievements silently skips
    # granting a code that has no matching Achievement row, same as
    # production would if the catalog were empty.
    headers = _signup_and_auth(client, "k@example.com", "completeuser")
    words = ["HELLO", "PLEASE", "THANKYOU"]
    last_body = None
    for w in words:
        resp = client.post(
            "/api/quests/greetings_quest/steps", json={"word": w, "self_correct": True}, headers=headers
        )
        last_body = resp.json()

    assert last_body["quest_completed"] is True
    assert last_body["quest"]["status"] == "completed"
    assert last_body["quest"]["completed_at"] is not None
    assert "Quest Starter" in last_body["new_achievements"]


def test_step_rejects_word_not_in_quest(client, seeded_quests):
    headers = _signup_and_auth(client, "l@example.com", "wrongworduser")
    resp = client.post(
        "/api/quests/greetings_quest/steps", json={"word": "WATER", "self_correct": True}, headers=headers
    )
    assert resp.status_code == 400


def test_unknown_quest_404s(client, seeded_quests):
    headers = _signup_and_auth(client, "m@example.com", "unknownuser")
    resp = client.get("/api/quests/not_a_real_quest", headers=headers)
    assert resp.status_code == 404
