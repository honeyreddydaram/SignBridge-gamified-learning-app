from datetime import datetime

from pydantic import BaseModel


class QuestWordStatus(BaseModel):
    word: str
    completed: bool
    mastery_state: str


class QuestOut(BaseModel):
    key: str
    quest_type: str
    title: str
    description: str
    prompt: str | None
    words: list[QuestWordStatus]
    status: str  # in_progress | completed
    completed_at: datetime | None


class QuestStepRequest(BaseModel):
    word: str
    self_correct: bool


class QuestStepResult(BaseModel):
    quest: QuestOut
    xp_awarded: int
    quest_completed: bool
    new_achievements: list[str]
