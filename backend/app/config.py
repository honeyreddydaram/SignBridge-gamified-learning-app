from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=str(BACKEND_DIR / ".env"), extra="ignore")

    database_url: str = "sqlite:///./signbridge.db"

    jwt_secret_key: str = "dev-only-insecure-secret-change-me"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    recognition_model_path: str = str(
        (BACKEND_DIR.parent / "ml" / "models" / "asl_landmark_classifier.joblib").resolve()
    )
    hand_landmarker_task_path: str = str(
        (BACKEND_DIR.parent / "ml" / "models" / "hand_landmarker.task").resolve()
    )
    recognition_confidence_threshold: float = 0.75

    frontend_origin: str = "http://localhost:5173"

    # Gamification tuning — centralized so lesson/quiz code doesn't hardcode magic numbers.
    starting_hearts: int = 5
    max_hearts: int = 5
    heart_regen_minutes: int = 30
    xp_per_correct_answer: int = 10
    xp_per_lesson_complete: int = 50
    xp_per_perfect_lesson: int = 25  # bonus on top of completion XP


@lru_cache
def get_settings() -> Settings:
    return Settings()
