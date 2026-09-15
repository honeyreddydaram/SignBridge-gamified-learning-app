"""
Structural validation of the real ml/word_signs_verified.json artifact
(not mocked) — catches corruption/regressions without hitting the network
(no live YouTube calls here; those were done manually during integration,
see ml/word_signs_research_report.md).
"""

import json

from app.asl_signs import VERIFIED_SIGNS_PATH, normalize_word

REQUIRED_FIELDS = {
    "word",
    "description",
    "video_provider",
    "video_id",
    "watch_url",
    "embed_url",
    "source_title",
    "source_channel",
}


def _load_raw():
    assert VERIFIED_SIGNS_PATH.exists(), (
        f"{VERIFIED_SIGNS_PATH} is missing — run the word-sign research pass "
        "or restore it before running this test."
    )
    return json.loads(VERIFIED_SIGNS_PATH.read_text(encoding="utf-8"))


def test_file_is_valid_json_array():
    data = _load_raw()
    assert isinstance(data, list)
    assert len(data) >= 100, f"expected >=100 verified words, got {len(data)}"


def test_every_entry_has_required_fields():
    for entry in _load_raw():
        missing = REQUIRED_FIELDS - entry.keys()
        assert not missing, f"{entry.get('word')} missing fields: {missing}"


def test_no_duplicate_words():
    words = [normalize_word(e["word"]) for e in _load_raw()]
    assert len(words) == len(set(words)), "duplicate word keys in word_signs_verified.json"


def test_all_video_urls_are_youtube_and_consistent():
    for entry in _load_raw():
        assert entry["video_provider"] == "youtube"
        vid = entry["video_id"]
        assert vid, f"{entry['word']} has empty video_id"
        assert entry["watch_url"] == f"https://www.youtube.com/watch?v={vid}"
        assert entry["embed_url"] == f"https://www.youtube.com/embed/{vid}"


def test_loaded_into_app_matches_file():
    from app.asl_signs import SUPPORTED_SIGNS

    raw = _load_raw()
    assert len(SUPPORTED_SIGNS) == len(raw)
    for entry in raw:
        word = normalize_word(entry["word"])
        assert word in SUPPORTED_SIGNS
        assert SUPPORTED_SIGNS[word].video_id == entry["video_id"]
