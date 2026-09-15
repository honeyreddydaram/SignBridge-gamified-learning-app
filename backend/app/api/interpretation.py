import re

from fastapi import APIRouter

from app.asl_signs import SUPPORTED_SIGNS, normalize_word
from app.schemas.interpretation import InterpretRequest, InterpretResponse, InterpretSegment, SignVideo

router = APIRouter(prefix="/api/interpretation", tags=["interpretation"])

DISCLAIMER = (
    "This shows English words fingerspelled letter-by-letter, plus a small set of "
    "recognized whole-word ASL signs (with real video of an actual signer). It does NOT "
    "produce grammatical ASL — ASL has its own grammar, word order, and non-manual markers "
    "(facial expression, body shift) that this tool does not model. Treat this as a "
    "fingerspelling/vocabulary aid, not a full translation."
)

_WORD_RE = re.compile(r"[A-Za-z']+")


def _to_video(sign) -> SignVideo:
    return SignVideo(
        provider=sign.video_provider,
        video_id=sign.video_id,
        watch_url=sign.watch_url,
        embed_url=sign.embed_url,
        source_title=sign.source_title,
        source_channel=sign.source_channel,
    )


@router.get("/supported-signs")
def list_supported_signs():
    """Browsable vocabulary list — used by a "supported words" browse view, and for
    sanity-checking coverage. Only words with a verified video appear here."""
    return {
        "count": len(SUPPORTED_SIGNS),
        "words": [
            {
                "word": sign.word,
                "description": sign.description,
                "source_channel": sign.source_channel,
            }
            for sign in sorted(SUPPORTED_SIGNS.values(), key=lambda s: s.word)
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
            if phrase_key in SUPPORTED_SIGNS:
                sign = SUPPORTED_SIGNS[phrase_key]
                segments.append(
                    InterpretSegment(
                        kind="sign",
                        word=f"{words[i].upper()} {words[i + 1].upper()}",
                        description=sign.description,
                        video=_to_video(sign),
                    )
                )
                i += 2
                continue

        norm = normalize_word(words[i])
        if not norm:
            i += 1
            continue

        if norm in SUPPORTED_SIGNS:
            sign = SUPPORTED_SIGNS[norm]
            segments.append(
                InterpretSegment(kind="sign", word=norm, description=sign.description, video=_to_video(sign))
            )
        else:
            segments.append(InterpretSegment(kind="fingerspell", word=norm, letters=list(norm)))
        i += 1

    return InterpretResponse(segments=segments, is_full_grammatical_asl=False, disclaimer=DISCLAIMER)
