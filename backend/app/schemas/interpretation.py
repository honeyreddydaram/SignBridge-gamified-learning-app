from pydantic import BaseModel, Field


class InterpretRequest(BaseModel):
    text: str = Field(min_length=1, max_length=500)


class InterpretSegment(BaseModel):
    kind: str  # "sign" | "fingerspell" | "space" | "skipped"
    word: str
    description: str | None = None  # populated for kind == "sign"
    letters: list[str] | None = None  # populated for kind == "fingerspell"


class InterpretResponse(BaseModel):
    segments: list[InterpretSegment]
    is_full_grammatical_asl: bool = False
    disclaimer: str
