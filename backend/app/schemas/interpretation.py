from pydantic import BaseModel, Field


class InterpretRequest(BaseModel):
    text: str = Field(min_length=1, max_length=500)


class SignVideo(BaseModel):
    provider: str  # currently always "youtube"
    video_id: str
    watch_url: str
    embed_url: str
    source_title: str
    source_channel: str


class InterpretSegment(BaseModel):
    kind: str  # "sign" | "fingerspell" | "space"
    word: str
    description: str | None = None  # populated for kind == "sign"
    video: SignVideo | None = None  # populated for kind == "sign" (real, verified video)
    letters: list[str] | None = None  # populated for kind == "fingerspell"


class InterpretResponse(BaseModel):
    segments: list[InterpretSegment]
    is_full_grammatical_asl: bool = False
    disclaimer: str
