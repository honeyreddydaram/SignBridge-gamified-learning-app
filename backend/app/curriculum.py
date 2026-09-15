"""
Static ASL fingerspelling curriculum content: one lesson per A-Z letter, with
a plain-language handshape description and programmatically generated quiz
exercises. This is hand-authored reference content (standard, widely
documented ASL fingerspelling handshapes) — not model output.

Visual "sign cards" are rendered by the frontend as SVG hand-skeleton
diagrams from ml/models/reference_landmarks.json (a real per-letter landmark
pose computed from the training dataset by ml/scripts/train.py), not stock
images, since the source dataset's license does not permit redistributing
its images.
"""

from __future__ import annotations

LETTERS = [chr(ord("A") + i) for i in range(26)]

LETTER_DESCRIPTIONS: dict[str, str] = {
    "A": "Make a fist with your thumb resting against the side of your index finger.",
    "B": "Hold your hand flat, fingers together pointing up, thumb folded across your palm.",
    "C": 'Curve your hand into a "C" shape, like holding a small cup.',
    "D": "Point your index finger straight up; touch thumb to middle finger, other fingers curled down.",
    "E": "Curl all fingertips down to touch the thumb pad.",
    "F": "Touch thumb and index fingertip together forming a circle; keep the other three fingers extended up.",
    "G": "Point index finger and thumb sideways, parallel to each other, other fingers closed.",
    "H": "Extend index and middle fingers together, pointing sideways, thumb tucked against the palm.",
    "I": "Make a fist with your pinky finger extended straight up.",
    "J": 'Like "I" (pinky extended), then trace the shape of a J in the air.',
    "K": "Point index and middle fingers up in a V, thumb touching the middle finger's base.",
    "L": "Extend thumb and index finger to form a clear L shape, other fingers folded into the palm.",
    "M": "Tuck your thumb under three fingers (index, middle, ring); pinky stays down.",
    "N": "Tuck your thumb under two fingers (index, middle); ring and pinky stay down.",
    "O": 'Curve all fingers and thumb to touch fingertip-to-thumb, forming an "O".',
    "P": "Like K but pointed downward: middle finger touches the thumb, index points down-forward.",
    "Q": "Like G but pointed downward: thumb and index finger extend down together.",
    "R": "Cross your index and middle fingers, other fingers folded down.",
    "S": "Make a fist with your thumb wrapped across the front of your fingers.",
    "T": "Make a fist with your thumb tucked between your index and middle fingers.",
    "U": "Extend index and middle fingers together, pointing straight up, other fingers folded.",
    "V": "Extend index and middle fingers apart in a V shape (peace sign).",
    "W": "Extend index, middle, and ring fingers spread apart; thumb holds the pinky down.",
    "X": "Make a fist with your index finger bent into a hook shape.",
    "Y": 'Extend thumb and pinky finger out ("hang loose" shape), other fingers folded.',
    "Z": "Extend your index finger and trace the shape of a Z in the air.",
}


def generate_lesson_exercises(letter: str, all_letters: list[str]) -> list[dict]:
    """
    Deterministic (seeded by letter) exercise set for a lesson:
      1. learn card
      2. sign-identification MCQ  (see a sign, pick the letter)
      3. letter-to-sign MCQ       (see a letter, pick the sign)
      4. camera challenge         (show the sign for X, validated by the recognition model)
    Distractors are chosen deterministically so the exercise set is stable
    across requests instead of silently changing under the user.
    """
    import random

    rng = random.Random(f"signbridge-{letter}")
    others = [l for l in all_letters if l != letter]
    distractors_1 = rng.sample(others, k=min(3, len(others)))
    distractors_2 = rng.sample(others, k=min(3, len(others)))

    return [
        {
            "type": "learn_card",
            "letter": letter,
            "description": LETTER_DESCRIPTIONS[letter],
        },
        {
            "type": "sign_identification_mcq",
            "prompt": "Which letter is this sign?",
            "shown_sign_letter": letter,
            "options": sorted([letter, *distractors_1], key=lambda _: rng.random()),
            "correct_option": letter,
        },
        {
            "type": "letter_to_sign_mcq",
            "prompt": f'Which sign represents the letter "{letter}"?',
            "shown_letter": letter,
            "options": sorted([letter, *distractors_2], key=lambda _: rng.random()),
            "correct_option": letter,
        },
        {
            "type": "camera_challenge",
            "prompt": f'Show the sign for "{letter}" to your camera.',
            "target_letter": letter,
        },
    ]
