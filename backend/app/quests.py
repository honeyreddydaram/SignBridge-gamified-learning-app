"""
Sign Quests: small, data-driven reinforcement missions over vocabulary
already taught elsewhere (Learning's vocabulary lessons) — not a new
teaching unit. New quests are added as data here, not new screens (see
api/quests.py, which is entirely generic over this list).

Two quest_types share one architecture per the same reasoning:
  - "mission": a checklist of words, one camera self-check per word
    (e.g. Greetings Quest: HELLO, PLEASE, THANKYOU)
  - "scenario": a short situational prompt expecting ONE concept, framed as
    "what would you sign here?" rather than a bare vocabulary drill

All quest camera steps are self-checked (learner marks their own attempt),
never model-graded — the trained recognition model only classifies static
A-Z handshapes and cannot validate these dynamic word signs. See
mastery_service.py's module docstring for the full rationale.
"""

from __future__ import annotations

from app.asl_signs import SUPPORTED_SIGNS

QUEST_DEFS: list[dict] = [
    {
        "key": "greetings_quest",
        "type": "mission",
        "title": "Greetings Quest",
        "description": "Sign the words you'd use to meet and thank someone.",
        "prompt": None,
        "words": ["HELLO", "PLEASE", "THANKYOU"],
    },
    {
        "key": "meet_someone_scenario",
        "type": "scenario",
        "title": "Meeting Someone New",
        "description": "A short situational challenge.",
        "prompt": "You meet someone for the first time. How would you greet them?",
        "words": ["HELLO"],
    },
    {
        "key": "receiving_gift_scenario",
        "type": "scenario",
        "title": "Someone Gives You Something",
        "description": "A short situational challenge.",
        "prompt": "Someone gives you something. What would you sign?",
        "words": ["THANKYOU"],
    },
]


def get_quest_defs() -> list[dict]:
    """Validates every quest word exists in the verified manifest before
    returning — same fail-loudly-at-call-time pattern as
    curriculum.get_vocabulary_categories()."""
    for quest in QUEST_DEFS:
        for word in quest["words"]:
            if word not in SUPPORTED_SIGNS:
                raise RuntimeError(
                    f"quests.py quest '{quest['key']}' references word '{word}' "
                    "which is not in SUPPORTED_SIGNS (ml/word_signs_verified.json)."
                )
    return QUEST_DEFS
