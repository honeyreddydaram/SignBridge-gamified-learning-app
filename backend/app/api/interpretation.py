import re

from fastapi import APIRouter

from app.asl_signs import SUPPORTED_SIGNS, normalize_word
from app.schemas.interpretation import InterpretRequest, InterpretResponse, InterpretSegment, SignVideo

router = APIRouter(prefix="/api/interpretation", tags=["interpretation"])

DISCLAIMER = (
    "This shows English words fingerspelled letter-by-letter, plus a small set of recognized "
    "whole-word ASL signs (real video of an actual signer). It does NOT produce grammatical ASL "
    "— ASL has its own grammar, word order, and non-manual markers (facial expression, body "
    "shift) that this tool does not model. Treat this as a communication aid for isolated "
    "words/signs, not a full translation."
)

_WORD_RE = re.compile(r"[A-Za-z']+")


def _to_video(sign) -> SignVideo:
    # loop_embed_url: YouTube's iframe API only loops a single video if you
    # pass playlist=<same video id> alongside loop=1 (a quirk of their embed
    # API — loop=1 alone loops the "next" video in an implicit playlist,
    # which for a lone video does nothing). controls/modestbranding/rel
    # strip down the player chrome for the clean, minimal-UI communication
    # use case this is built for.
    return SignVideo(
        provider=sign.video_provider,
        video_id=sign.video_id,
        watch_url=sign.watch_url,
        embed_url=sign.embed_url,
        loop_embed_url=(
            f"{sign.embed_url}?autoplay=1&mute=1&loop=1&playlist={sign.video_id}"
            "&controls=0&rel=0&modestbranding=1&playsinline=1"
        ),
        source_title=sign.source_title,
        source_channel=sign.source_channel,
    )


def _is_communication_ready(sign) -> bool:
    """
    Communication-mode playback (Interpretation module) is restricted to
    words backed by a video dedicated to just that one sign. Many manifest
    entries are compilation videos shared by several words (e.g. one
    "Colors" video backs all 10 colors) — looping the WHOLE video to
    "communicate" a single word would show unrelated signs too, which is
    wrong for a communication tool (it's fine for Learning, where seeing
    neighboring vocabulary in context is a feature, not a bug — see
    curriculum.py's vocab_video_card, which uses the same manifest entries
    without this restriction).
    """
    return sign.is_dedicated_video


@router.get("/supported-signs")
def list_supported_signs():
    """Words with clean, communication-ready single-sign video (used by the
    Interpretation module). For the full 114-word teaching vocabulary
    (including compilation-video entries), see the Learning module's
    vocabulary lessons instead — same underlying manifest, different
    playback use case."""
    ready = [s for s in SUPPORTED_SIGNS.values() if _is_communication_ready(s)]
    return {
        "count": len(ready),
        "total_vocabulary_count": len(SUPPORTED_SIGNS),
        "words": [
            {"word": sign.word, "source_channel": sign.source_channel}
            for sign in sorted(ready, key=lambda s: s.word)
        ],
    }


@router.post("/interpret", response_model=InterpretResponse)
def interpret(payload: InterpretRequest):
    words = _WORD_RE.findall(payload.text)

    segments: list[InterpretSegment] = []
    i = 0
    while i < len(words):
        # Greedy longest-match: try a two-word phrase (e.g. "thank you") before
        # falling back to a single word, so multi-word signs are recognized
        # without requiring the user to type them as one word.
        if i + 1 < len(words):
            phrase_key = normalize_word(words[i] + words[i + 1])
            sign = SUPPORTED_SIGNS.get(phrase_key)
            if sign and _is_communication_ready(sign):
                segments.append(
                    InterpretSegment(kind="sign", word=f"{words[i].upper()} {words[i + 1].upper()}", video=_to_video(sign))
                )
                i += 2
                continue

        norm = normalize_word(words[i])
        if not norm:
            i += 1
            continue

        sign = SUPPORTED_SIGNS.get(norm)
        if sign and _is_communication_ready(sign):
            segments.append(InterpretSegment(kind="sign", word=norm, video=_to_video(sign)))
        else:
            segments.append(InterpretSegment(kind="fingerspell", word=norm, letters=list(norm)))
        i += 1

    return InterpretResponse(segments=segments, is_full_grammatical_asl=False, disclaimer=DISCLAIMER)
