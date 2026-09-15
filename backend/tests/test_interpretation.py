def test_supported_word_is_marked_as_sign_not_fingerspell(client):
    resp = client.post("/api/interpretation/interpret", json={"text": "hello"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["is_full_grammatical_asl"] is False
    assert len(body["disclaimer"]) > 0
    segments = [s for s in body["segments"] if s["kind"] != "space"]
    assert segments[0]["kind"] == "sign"
    assert segments[0]["word"] == "HELLO"


def test_unsupported_word_falls_back_to_fingerspelling(client):
    resp = client.post("/api/interpretation/interpret", json={"text": "xylophone"})
    body = resp.json()
    segments = [s for s in body["segments"] if s["kind"] != "space"]
    assert segments[0]["kind"] == "fingerspell"
    assert segments[0]["letters"] == list("XYLOPHONE")


def test_mixed_sentence_produces_both_kinds(client):
    resp = client.post("/api/interpretation/interpret", json={"text": "hello xyz"})
    body = resp.json()
    kinds = [s["kind"] for s in body["segments"] if s["kind"] != "space"]
    assert kinds == ["sign", "fingerspell"]


def test_empty_text_rejected(client):
    resp = client.post("/api/interpretation/interpret", json={"text": ""})
    assert resp.status_code == 422
