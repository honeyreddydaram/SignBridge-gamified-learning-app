"""
Curated dictionary of common single-word ASL signs, for the word/phrase-level
interpretation layer described in the project spec.

IMPORTANT — scope and honesty boundary:
This is a small, hand-curated reference dictionary of common, widely-taught
ASL signs (general knowledge, consistent with public ASL education resources
such as Lifeprint.com and Handspeak.com). It is NOT a validated, certified,
or exhaustive ASL dictionary, and English word order is NOT ASL grammar (ASL
uses its own grammar, classifiers, and non-manual markers this system does
not model). Any word not in SUPPORTED_SIGNS falls back to fingerspelling.
Users should treat descriptions as a learning aid, not authoritative
instruction — a disclaimer to that effect is surfaced in the UI.
"""

from __future__ import annotations

SUPPORTED_SIGNS: dict[str, str] = {
    "HELLO": "Flat hand starts near the forehead/temple and moves outward and away, like a small salute.",
    "HI": "Same as HELLO: flat hand near the forehead moves outward.",
    "GOODBYE": "Wave the open hand side to side, or open/close the fingers toward the palm (\"bye-bye\" wave).",
    "BYE": "Wave the open hand side to side.",
    "PLEASE": "Flat hand rubs in a circular motion on the chest.",
    "THANKYOU": "Flat hand touches the chin, then moves forward and down toward the person you're thanking.",
    "SORRY": "Fist makes a circular motion on the chest (like rubbing).",
    "YES": "Fist nods up and down at the wrist, like a head nodding yes.",
    "NO": "Index and middle finger snap closed against the thumb, like a small \"no\" peck.",
    "HELP": "One flat hand (fist on top) is lifted upward by the other flat hand underneath it.",
    "NAME": "Index and middle fingers of one hand tap across index and middle fingers of the other, forming an X twice.",
    "WANT": "Both hands, palms up and fingers curled, pull inward toward the body.",
    "LOVE": "Cross both fists over the chest, as if hugging yourself.",
    "MORE": "Fingertips of both flat/curved hands tap together repeatedly.",
    "STOP": "The edge of one flat hand chops down onto the open palm of the other.",
    "GO": "Both index fingers, bent, point forward and flick forward in the direction of motion.",
    "EAT": "Fingertips of one hand, gathered together, tap toward the mouth repeatedly.",
    "DRINK": "Hand forms a \"C\" as if holding a cup, tips toward the mouth.",
    "WATER": "\"W\" handshape (index, middle, ring fingers up) taps the chin.",
    "FRIEND": "Index fingers of both hands hook together, then reverse and hook again.",
    "GOOD": "Flat hand touches the chin, then moves down and out into the other open palm.",
    "BAD": "Flat hand touches the chin, then flips downward and outward (opposite of GOOD).",
    "FINISHED": "Both open hands, palms facing you, flip outward to face away in one quick motion.",
    "DONE": "Same as FINISHED.",
    "LEARN": "Fingertips of one hand \"pick up\" information from the open palm and move it to the forehead.",
    "PRACTICE": "One fist (like an \"A\") rubs back and forth along the other index finger.",
    "AGAIN": "Bent fingers of one hand arc over and tap into the open palm of the other.",
    "SIGN": "Both index fingers alternately circle around each other in front of the body.",
    "LANGUAGE": "Both \"L\" handshapes, fingertips touching, twist apart from each other.",
    "UNDERSTAND": "A bent index finger flicks upward near the forehead, like a lightbulb of realization.",
}


def normalize_word(word: str) -> str:
    return "".join(ch for ch in word.upper() if ch.isalpha())
