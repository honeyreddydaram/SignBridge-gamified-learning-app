from pydantic import BaseModel, Field


class SignInteractionRequest(BaseModel):
    word: str = Field(min_length=1, max_length=50)
    interaction_type: str  # "viewed" | "recognize" | "produce_selfcheck" | "recall_selfcheck"
    correct: bool | None = None


class SignInteractionResult(BaseModel):
    word: str
    state: str
    just_mastered: bool
    xp_awarded: int
    new_achievements: list[str]
    level: int
    xp_total: int


class MasterySummary(BaseModel):
    new: int
    learning: int
    practicing: int
    mastered: int
    needs_practice: list[str]
