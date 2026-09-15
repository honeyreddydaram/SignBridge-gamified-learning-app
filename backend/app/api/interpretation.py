import re

from fastapi import APIRouter

from app.asl_signs import SUPPORTED_SIGNS, normalize_word
from app.schemas.interpretation import InterpretRequest, InterpretResponse, InterpretSegment

router = APIRouter(prefix="/api/interpretation", tags=["interpretation"])

DISCLAIMER = (
    "This shows English words fingerspelled letter-by-letter, plus a small set of "
    "recognized whole-word ASL signs. It does NOT produce grammatical ASL — ASL has its "
    "own grammar, word order, and non-manual markers (facial expression, body shift) that "
    "this tool does not model. Treat this as a fingerspelling/vocabulary aid, not a full translation."
)


@router.get("/supported-signs")
def list_supported_signs():
    return {"count": len(SUPPORTED_SIGNS), "words": sorted(SUPPORTED_SIGNS.keys())}


@router.post("/interpret", response_model=InterpretResponse)
def interpret(payload: InterpretRequest):
    tokens = re.findall(r"[A-Za-z]+|\s+", payload.text)

    segments: list[InterpretSegment] = []
    for tok in tokens:
        if tok.isspace():
            segments.append(InterpretSegment(kind="space", word=" "))
            continue

        norm = normalize_word(tok)
        if not norm:
            continue

        if norm in SUPPORTED_SIGNS:
            segments.append(
                InterpretSegment(kind="sign", word=norm, description=SUPPORTED_SIGNS[norm])
            )
        else:
            segments.append(
                InterpretSegment(kind="fingerspell", word=norm, letters=list(norm))
            )

    return InterpretResponse(segments=segments, is_full_grammatical_asl=False, disclaimer=DISCLAIMER)
