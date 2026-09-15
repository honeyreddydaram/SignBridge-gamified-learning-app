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

from app.asl_signs import SUPPORTED_SIGNS

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


# ---------------------------------------------------------------------------
# Vocabulary track: thematic lessons built from the verified 114-word sign
# manifest (ml/word_signs_verified.json, loaded via app.asl_signs). Every
# word below MUST exist in SUPPORTED_SIGNS — see the assertion in
# get_vocabulary_categories(), which fails loudly at import time rather than
# silently dropping a mistyped word.
#
# NOTE ON CAMERA CHALLENGES: unlike the alphabet track, vocabulary lessons do
# NOT include a recognition-model-graded camera challenge. The trained
# recognition model (ml/models/asl_landmark_classifier.joblib) only
# classifies static A-Z fingerspelling handshapes from a single frame — it
# was never trained on, and cannot validate, dynamic multi-frame word-level
# signs like HELLO or THANK YOU. Claiming to auto-grade those would be
# exactly the kind of fabricated-working-feature this project explicitly
# rules out. Instead, camera steps in the Learn -> Recognize -> Produce ->
# Recall loop below ("vocab_produce_selfcheck", "vocab_recall_selfcheck")
# are always SELF-checked: the learner's own camera feed, and the learner
# (not the model) marks whether they got it right. See
# generate_vocabulary_exercises() and mastery_service.py for how that feeds
# mastery state. Sign Quests (app/quests.py) and scenarios follow the same
# self-check rule.
# ---------------------------------------------------------------------------

VOCABULARY_CATEGORIES: list[dict] = [
    {
        "key": "greetings_courtesy",
        "title": "Greetings & Courtesy",
        "description": "The everyday words you'll use to start and end a conversation politely.",
        "words": ["HELLO", "HI", "GOODBYE", "BYE", "PLEASE", "THANKYOU", "SORRY", "WELCOME", "YES", "NO", "MAYBE"],
    },
    {
        "key": "family_people",
        "title": "Family & People",
        "description": "People words: family members, pronouns, and common roles.",
        "words": [
            "MOTHER", "FATHER", "GRANDMOTHER", "GRANDFATHER", "BROTHER", "SISTER", "FAMILY", "FRIEND",
            "BABY", "MAN", "WOMAN", "BOY", "GIRL", "TEACHER", "STUDENT", "I", "ME", "YOU", "WE", "THEY",
        ],
    },
    {
        "key": "needs_requests",
        "title": "Needs & Requests",
        "description": "Say what you want, need, or are asking someone to do.",
        "words": ["WANT", "NEED", "LIKE", "HELP", "MORE", "STOP", "FINISHED", "DONE", "GO", "COME", "WAIT", "AGAIN", "GIVE", "TAKE"],
    },
    {
        "key": "feelings_emotions",
        "title": "Feelings & Emotions",
        "description": "Describe how you or someone else is feeling.",
        "words": ["HAPPY", "SAD", "ANGRY", "TIRED", "HUNGRY", "THIRSTY", "SCARED", "EXCITED", "LOVE"],
    },
    {
        "key": "question_words",
        "title": "Question Words",
        "description": "The six core question words used to ask for information.",
        "words": ["WHO", "WHAT", "WHEN", "WHERE", "WHY", "HOW"],
    },
    {
        "key": "everyday_actions",
        "title": "Everyday Actions",
        "description": "Common verbs for daily activities and communication.",
        "words": [
            "EAT", "DRINK", "SIT", "STAND", "WALK", "RUN", "PLAY", "WORK", "SLEEP", "CLEAN",
            "UNDERSTAND", "KNOW", "THINK", "REMEMBER", "FORGET", "SEE", "LOOK", "TALK", "SPEAK", "ASK", "NAME",
        ],
    },
    {
        "key": "descriptions_opposites",
        "title": "Descriptions & Opposites",
        "description": "Descriptive words, often useful in opposite pairs.",
        "words": ["RIGHT", "WRONG", "SAME", "DIFFERENT", "OLD", "BIG", "SMALL", "HOT", "COLD", "SLOW", "OPEN", "CLOSE", "FUNNY", "BEAUTIFUL"],
    },
    {
        "key": "colors",
        "title": "Colors",
        "description": "The ten basic colors.",
        "words": ["RED", "BLUE", "GREEN", "YELLOW", "BLACK", "WHITE", "BROWN", "ORANGE", "PURPLE", "PINK"],
    },
    {
        "key": "time_words",
        "title": "Time Words",
        "description": "Talk about when something happens.",
        "words": ["TIME", "TODAY", "TOMORROW", "YESTERDAY"],
    },
    {
        "key": "home_things",
        "title": "Home & Everyday Things",
        "description": "Common nouns for places and things around you.",
        "words": ["HOME", "HOUSE", "FOOD", "WATER", "MONEY"],
    },
]


def get_vocabulary_categories() -> list[dict]:
    """Validates every category word actually exists in the verified manifest
    before returning — fails loudly at call time rather than silently
    generating a lesson with a missing sign."""
    for cat in VOCABULARY_CATEGORIES:
        for word in cat["words"]:
            if word not in SUPPORTED_SIGNS:
                raise RuntimeError(
                    f"curriculum.py vocabulary category '{cat['key']}' references word "
                    f"'{word}' which is not in SUPPORTED_SIGNS (ml/word_signs_verified.json). "
                    "Fix the category list or the manifest."
                )
    return VOCABULARY_CATEGORIES


def _video_dict(sign) -> dict:
    return {
        "provider": sign.video_provider,
        "video_id": sign.video_id,
        "watch_url": sign.watch_url,
        "embed_url": sign.embed_url,
        "source_title": sign.source_title,
        "source_channel": sign.source_channel,
    }


def _mcq_for_word(word: str, all_words: list[str], rng) -> dict:
    sign = SUPPORTED_SIGNS[word]
    others = [w for w in all_words if w != word]
    distractors = rng.sample(others, k=min(3, len(others)))
    return {
        "type": "vocab_comprehension_mcq",
        "prompt": "What does this sign mean?",
        "video": _video_dict(sign),
        "options": sorted([word, *distractors], key=lambda _: rng.random()),
        "correct_option": word,
    }


def generate_vocabulary_exercises(category_key: str, mastery_by_word: dict[str, str] | None = None) -> list[dict]:
    """
    Per-word exercise sequence implementing the Learn -> Recognize ->
    Produce -> Recall loop, branched by each word's current mastery state
    (`mastery_by_word`: word -> "new"|"learning"|"practicing"|"mastered",
    from UserSignMastery; a word with no entry is treated as "new"):

      new / learning -> Learn (vocab_video_card) -> Recognize
                         (vocab_comprehension_mcq) -> Produce
                         (vocab_produce_selfcheck)
      practicing     -> Recall only (vocab_recall_selfcheck) — no demo shown
                         first, since Recall specifically tests memory, not
                         imitation
      mastered       -> skipped (nothing left to teach); if EVERY word in
                         the category is already mastered, falls back to a
                         full Recall pass over all of them instead of
                         returning an empty/broken lesson

    Produce and Recall are ALWAYS self-checked, never model-graded — see
    this module's docstring for why (the trained recognition model can't
    validate dynamic word-level signs).
    """
    import random

    category = next((c for c in get_vocabulary_categories() if c["key"] == category_key), None)
    if category is None:
        raise ValueError(f"unknown vocabulary category: {category_key}")

    words = category["words"]
    all_words = [w for cat in VOCABULARY_CATEGORIES for w in cat["words"]]
    rng = random.Random(f"signbridge-vocab-{category_key}")
    mastery_by_word = mastery_by_word or {}

    def state_of(word: str) -> str:
        return mastery_by_word.get(word, "new")

    exercises: list[dict] = []
    for word in words:
        state = state_of(word)
        sign = SUPPORTED_SIGNS[word]

        if state == "mastered":
            continue

        if state == "practicing":
            exercises.append(
                {
                    "type": "vocab_recall_selfcheck",
                    "word": word,
                    "prompt": f'From memory — show the sign for "{word}" (no demo shown, this tests recall).',
                }
            )
            continue

        # new / learning: full Learn -> Recognize -> Produce
        exercises.append(
            {
                "type": "vocab_video_card",
                "word": word,
                "description": sign.description,
                "video": _video_dict(sign),
                "source_channel": sign.source_channel,
            }
        )
        exercises.append(_mcq_for_word(word, all_words, rng))
        exercises.append(
            {
                "type": "vocab_produce_selfcheck",
                "word": word,
                "prompt": f'Your turn — show the sign for "{word}".',
            }
        )

    if not exercises:
        # Every word already mastered: still give a lesson (a full Recall
        # review) rather than returning nothing.
        for word in words:
            exercises.append(
                {
                    "type": "vocab_recall_selfcheck",
                    "word": word,
                    "prompt": f'Review — from memory, show the sign for "{word}".',
                }
            )

    return exercises
