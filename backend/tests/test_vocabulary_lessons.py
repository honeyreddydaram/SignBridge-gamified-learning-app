def _signup_and_auth(client, email="vocab@example.com", username="vocablearner"):
    resp = client.post("/api/auth/signup", json={"email": email, "username": username, "password": "password123"})
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_alphabet_and_vocabulary_tracks_unlock_independently(client, seeded_curriculum, seeded_vocabulary):
    headers = _signup_and_auth(client)
    lessons = client.get("/api/lessons", headers=headers).json()

    alphabet = [l for l in lessons if l["lesson_type"] == "alphabet"]
    vocabulary = [l for l in lessons if l["lesson_type"] == "vocabulary"]
    assert len(alphabet) == 26
    assert len(vocabulary) == 10

    # First lesson of EACH track is unlocked independently — neither track
    # gates the other.
    assert alphabet[0]["status"] == "unlocked"
    assert all(l["status"] == "locked" for l in alphabet[1:])
    assert vocabulary[0]["status"] == "unlocked"
    assert all(l["status"] == "locked" for l in vocabulary[1:])


def test_vocabulary_lesson_exercises_shape(client, seeded_curriculum, seeded_vocabulary):
    headers = _signup_and_auth(client, "v2@example.com", "vocab2")
    lessons = client.get("/api/lessons", headers=headers).json()
    vocab_lesson = next(l for l in lessons if l["lesson_type"] == "vocabulary")

    resp = client.get(f"/api/lessons/{vocab_lesson['id']}/exercises", headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    exercises = body["exercises"]

    video_cards = [e for e in exercises if e["type"] == "vocab_video_card"]
    mcqs = [e for e in exercises if e["type"] == "vocab_comprehension_mcq"]
    mirror = [e for e in exercises if e["type"] == "vocab_mirror_practice"]

    assert len(video_cards) == len(mcqs)  # one MCQ per word
    assert len(mirror) == 1
    assert exercises[-1]["type"] == "vocab_mirror_practice"

    # Every video card must carry a real verified video, not a fabricated one.
    for card in video_cards:
        assert card["video"]["video_id"]
        assert card["video"]["provider"] == "youtube"


def test_complete_vocabulary_lesson_unlocks_next_within_track_only(client, seeded_curriculum, seeded_vocabulary):
    headers = _signup_and_auth(client, "v3@example.com", "vocab3")
    lessons = client.get("/api/lessons", headers=headers).json()
    first_vocab = next(l for l in lessons if l["lesson_type"] == "vocabulary" and l["order_index"] == 1)

    resp = client.post(
        f"/api/lessons/{first_vocab['id']}/complete",
        json={"correct_count": 10, "total_count": 10},
        headers=headers,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["lesson"]["status"] == "completed"
    assert body["xp_awarded"] == 75  # same XP rules as alphabet track

    lessons_after = client.get("/api/lessons", headers=headers).json()
    alphabet_after = [l for l in lessons_after if l["lesson_type"] == "alphabet"]
    vocabulary_after = [l for l in lessons_after if l["lesson_type"] == "vocabulary"]

    # Completing vocabulary lesson 1 unlocks vocabulary lesson 2...
    assert vocabulary_after[1]["status"] == "unlocked"
    # ...but must NOT unlock anything in the alphabet track (still only
    # alphabet lesson 1 unlocked, exactly as before).
    assert alphabet_after[0]["status"] == "unlocked"
    assert all(l["status"] == "locked" for l in alphabet_after[1:])


def test_alphabet_complete_achievement_not_triggered_by_vocabulary_completions(
    client, seeded_curriculum, seeded_vocabulary
):
    """Regression test: completing lessons across both tracks must not
    accidentally satisfy the alphabet-specific achievement threshold."""
    headers = _signup_and_auth(client, "v4@example.com", "vocab4")
    lessons = client.get("/api/lessons", headers=headers).json()
    vocab_lessons = sorted(
        [l for l in lessons if l["lesson_type"] == "vocabulary"], key=lambda l: l["order_index"]
    )

    all_achievements: list[str] = []
    for lesson in vocab_lessons:
        # re-fetch to get freshly-unlocked next lesson id each iteration
        current = client.get("/api/lessons", headers=headers).json()
        lesson = next(l for l in current if l["id"] == lesson["id"])
        if lesson["status"] == "locked":
            continue
        resp = client.post(
            f"/api/lessons/{lesson['id']}/complete", json={"correct_count": 5, "total_count": 5}, headers=headers
        )
        all_achievements.extend(resp.json()["new_achievements"])

    assert "Alphabet Master" not in all_achievements
    assert "Vocabulary Builder" in all_achievements
