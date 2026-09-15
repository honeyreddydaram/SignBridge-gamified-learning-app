from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.lesson import LessonStatus


class LessonOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    letter: str
    order_index: int
    title: str
    description: str
    status: LessonStatus
    best_score_pct: int
    attempts: int
    completed_at: datetime | None


class QuizAnswerSubmission(BaseModel):
    question_index: int
    selected_option: str
    correct: bool


class LessonCompletionRequest(BaseModel):
    correct_count: int
    total_count: int


class LessonCompletionResult(BaseModel):
    lesson: LessonOut
    xp_awarded: int
    newly_unlocked_lesson_ids: list[int]
    new_achievements: list[str]
    leveled_up: bool
    level: int
    xp_total: int
