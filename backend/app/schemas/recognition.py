from pydantic import BaseModel


class RecognitionRequest(BaseModel):
    # Base64-encoded JPEG/PNG frame, e.g. "data:image/jpeg;base64,/9j/4AAQ..."
    image_base64: str
    # If set, this is a directed practice/challenge attempt ("show the sign for X")
    target_letter: str | None = None
    lesson_id: int | None = None


class RecognitionResult(BaseModel):
    hand_detected: bool
    predicted_letter: str | None
    confidence: float
    is_confident: bool
    correct: bool | None = None  # only meaningful when target_letter was supplied
