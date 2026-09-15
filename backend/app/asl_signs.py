"""
Vocabulary of common single-word/phrase ASL signs, for the word/phrase-level
interpretation layer described in the project spec.

IMPORTANT — scope and honesty boundary:
Each entry's video is a REAL, individually-verified recording of an actual
signer, sourced from a reputable ASL-education channel and embedded via that
platform's official embed mechanism (never re-hosted/redistributed) — see
`ml/word_signs_research_report.md` for exactly how each one was verified and
which source(s) were used. A word with no verified video is NOT considered
"supported" and falls back to fingerspelling, even if we have a text
description for it — we do not show a "Supported ASL sign" badge backed by
nothing but a guess. English word order is also NOT ASL grammar (ASL has its
own grammar, classifiers, and non-manual markers this system does not
model) — that disclaimer is surfaced in the UI regardless of video coverage.

Data source: ml/word_signs_verified.json (produced by the research/
verification pass — see ml/word_signs_research_report.md). This module just
loads and validates that file; it does not itself decide what counts as
verified.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)

VERIFIED_SIGNS_PATH = Path(__file__).resolve().parent.parent.parent / "ml" / "word_signs_verified.json"

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


@dataclass(frozen=True)
class WordSign:
    word: str
    description: str
    video_provider: str
    video_id: str
    watch_url: str
    embed_url: str
    source_title: str
    source_channel: str
    verification_method: str = ""
    notes: str = ""
    # True if this video_id appears under exactly one word in the whole
    # manifest (not a compilation shared by several words, e.g. one "Colors"
    # video backing all 10 colors). Computed at load time, not stored in the
    # source JSON. This matters because a shared/compilation video can't be
    # cleanly looped to show just ONE sign — looping it plays neighboring
    # signs too. The Learning module is fine with that (full context is
    # useful for teaching); the Interpretation module's clean-loop
    # "communication" playback is restricted to is_dedicated_video=True
    # words for exactly this reason — see interpretation.py.
    is_dedicated_video: bool = False


def _load_verified_signs() -> dict[str, WordSign]:
    if not VERIFIED_SIGNS_PATH.exists():
        logger.warning(
            "No verified word-sign video data at %s — all words will fall back to "
            "fingerspelling until the research/verification pass runs. See ml/README.md.",
            VERIFIED_SIGNS_PATH,
        )
        return {}

    try:
        raw = json.loads(VERIFIED_SIGNS_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as e:
        logger.error("Failed to load %s: %s — treating vocabulary as empty.", VERIFIED_SIGNS_PATH, e)
        return {}

    valid_entries = []
    for entry in raw:
        missing = REQUIRED_FIELDS - entry.keys()
        if missing:
            logger.warning("Skipping word-sign entry missing fields %s: %r", missing, entry.get("word"))
            continue
        word = normalize_word(entry["word"])
        if not word:
            continue
        valid_entries.append((word, entry))

    video_id_counts: dict[str, int] = {}
    for _, entry in valid_entries:
        video_id_counts[entry["video_id"]] = video_id_counts.get(entry["video_id"], 0) + 1

    signs: dict[str, WordSign] = {}
    for word, entry in valid_entries:
        signs[word] = WordSign(
            word=word,
            description=entry["description"],
            video_provider=entry["video_provider"],
            video_id=entry["video_id"],
            watch_url=entry["watch_url"],
            embed_url=entry["embed_url"],
            source_title=entry["source_title"],
            source_channel=entry["source_channel"],
            verification_method=entry.get("verification_method", ""),
            notes=entry.get("notes", ""),
            is_dedicated_video=video_id_counts[entry["video_id"]] == 1,
        )
    return signs


def normalize_word(word: str) -> str:
    return "".join(ch for ch in word.upper() if ch.isalpha())


# Loaded once at import time. Reload requires a process restart — this is a
# small, infrequently-changing reference dataset, not live application data.
SUPPORTED_SIGNS: dict[str, WordSign] = _load_verified_signs()
