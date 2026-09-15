import pytest

from app.asl_signs import SUPPORTED_SIGNS, WordSign


@pytest.fixture(autouse=True)
def _fake_vocabulary():
    """
    Interpretation tests must not depend on the real, externally-researched
    ml/word_signs_verified.json (it may be absent, partial, or change over
    time) — inject a small deterministic fixture instead. SUPPORTED_SIGNS is
    mutated in place (not reassigned) so the same dict object already
    imported by app.api.interpretation sees the change, and the original
    contents are restored afterward so later tests (e.g.
    test_word_signs_data.py) still see the real loaded vocabulary.
    """
    original = dict(SUPPORTED_SIGNS)
    SUPPORTED_SIGNS.clear()
    SUPPORTED_SIGNS["HELLO"] = WordSign(
        word="HELLO",
        description="Flat hand starts near the forehead and moves outward.",
        video_provider="youtube",
        video_id="fake_id_123",
        watch_url="https://www.youtube.com/watch?v=fake_id_123",
        embed_url="https://www.youtube.com/embed/fake_id_123",
        source_title="How to Sign Hello in ASL",
        source_channel="Test Channel",
    )
    SUPPORTED_SIGNS["THANKYOU"] = WordSign(
        word="THANKYOU",
        description="Flat hand touches the chin, then moves forward toward the person.",
        video_provider="youtube",
        video_id="fake_id_456",
        watch_url="https://www.youtube.com/watch?v=fake_id_456",
        embed_url="https://www.youtube.com/embed/fake_id_456",
        source_title="How to Sign Thank You in ASL",
        source_channel="Test Channel",
    )
    yield
    SUPPORTED_SIGNS.clear()
    SUPPORTED_SIGNS.update(original)


def test_supported_word_is_marked_as_sign_with_video(client):
    resp = client.post("/api/interpretation/interpret", json={"text": "hello"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["is_full_grammatical_asl"] is False
    assert len(body["disclaimer"]) > 0
    segments = [s for s in body["segments"] if s["kind"] != "space"]
    assert segments[0]["kind"] == "sign"
    assert segments[0]["word"] == "HELLO"
    assert segments[0]["video"]["video_id"] == "fake_id_123"
    assert segments[0]["video"]["provider"] == "youtube"


def test_two_word_phrase_matches_before_falling_back(client):
    resp = client.post("/api/interpretation/interpret", json={"text": "thank you"})
    body = resp.json()
    segments = [s for s in body["segments"] if s["kind"] != "space"]
    assert len(segments) == 1
    assert segments[0]["kind"] == "sign"
    assert segments[0]["word"] == "THANK YOU"
    assert segments[0]["video"]["video_id"] == "fake_id_456"


def test_unsupported_word_falls_back_to_fingerspelling(client):
    resp = client.post("/api/interpretation/interpret", json={"text": "xylophone"})
    body = resp.json()
    segments = [s for s in body["segments"] if s["kind"] != "space"]
    assert segments[0]["kind"] == "fingerspell"
    assert segments[0]["letters"] == list("XYLOPHONE")
    assert segments[0]["video"] is None


def test_mixed_sentence_produces_both_kinds(client):
    resp = client.post("/api/interpretation/interpret", json={"text": "hello xyz"})
    body = resp.json()
    kinds = [s["kind"] for s in body["segments"] if s["kind"] != "space"]
    assert kinds == ["sign", "fingerspell"]


def test_word_without_verified_video_is_not_supported(client):
    """A word absent from SUPPORTED_SIGNS must fingerspell, never show a fabricated sign."""
    resp = client.post("/api/interpretation/interpret", json={"text": "friend"})
    body = resp.json()
    segments = [s for s in body["segments"] if s["kind"] != "space"]
    assert segments[0]["kind"] == "fingerspell"


def test_empty_text_rejected(client):
    resp = client.post("/api/interpretation/interpret", json={"text": ""})
    assert resp.status_code == 422


def test_supported_signs_listing(client):
    resp = client.get("/api/interpretation/supported-signs")
    assert resp.status_code == 200
    body = resp.json()
    assert body["count"] == 2
    words = [w["word"] for w in body["words"]]
    assert "HELLO" in words and "THANKYOU" in words
