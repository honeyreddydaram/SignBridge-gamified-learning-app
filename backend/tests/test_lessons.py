def _signup_and_auth(client, email="learner@example.com", username="learner"):
    resp = client.post("/api/auth/signup", json={"email": email, "username": username, "password": "password123"})
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_first_lesson_unlocked_rest_locked(client, seeded_curriculum):
    headers = _signup_and_auth(client)
    resp = client.get("/api/lessons", headers=headers)
    assert resp.status_code == 200
    lessons = resp.json()
    assert len(lessons) == 26
    assert lessons[0]["status"] == "unlocked"
    assert all(l["status"] == "locked" for l in lessons[1:])


def test_locked_lesson_exercises_forbidden(client, seeded_curriculum):
    headers = _signup_and_auth(client, "l2@example.com", "learner2")
    resp = client.get("/api/lessons", headers=headers)
    second_lesson_id = resp.json()[1]["id"]
    resp = client.get(f"/api/lessons/{second_lesson_id}/exercises", headers=headers)
    assert resp.status_code == 403


def test_complete_lesson_unlocks_next_and_awards_xp(client, seeded_curriculum):
    headers = _signup_and_auth(client, "l3@example.com", "learner3")
    lessons = client.get("/api/lessons", headers=headers).json()
    first_id = lessons[0]["id"]

    resp = client.post(f"/api/lessons/{first_id}/complete", json={"correct_count": 4, "total_count": 4}, headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["lesson"]["status"] == "completed"
    assert body["xp_awarded"] == 75  # 50 base + 25 perfect-score bonus
    assert len(body["newly_unlocked_lesson_ids"]) == 1
    assert "First Steps" in body["new_achievements"]
    assert "Perfectionist" in body["new_achievements"]

    lessons_after = client.get("/api/lessons", headers=headers).json()
    assert lessons_after[1]["status"] == "unlocked"


def test_complete_lesson_twice_does_not_double_award_xp(client, seeded_curriculum):
    headers = _signup_and_auth(client, "l4@example.com", "learner4")
    lessons = client.get("/api/lessons", headers=headers).json()
    first_id = lessons[0]["id"]

    client.post(f"/api/lessons/{first_id}/complete", json={"correct_count": 4, "total_count": 4}, headers=headers)
    resp = client.post(f"/api/lessons/{first_id}/complete", json={"correct_count": 2, "total_count": 4}, headers=headers)
    assert resp.status_code == 200
    assert resp.json()["xp_awarded"] == 0  # already completed once — no repeat XP

    me = client.get("/api/users/me", headers=headers).json()
    assert me["xp_total"] == 75


def test_complete_lesson_invalid_counts_rejected(client, seeded_curriculum):
    headers = _signup_and_auth(client, "l5@example.com", "learner5")
    lessons = client.get("/api/lessons", headers=headers).json()
    first_id = lessons[0]["id"]

    resp = client.post(f"/api/lessons/{first_id}/complete", json={"correct_count": 5, "total_count": 4}, headers=headers)
    assert resp.status_code == 400
