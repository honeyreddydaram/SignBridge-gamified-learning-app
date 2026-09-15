from datetime import date, datetime

from pydantic import BaseModel, ConfigDict


class UserProfile(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    username: str
    created_at: datetime
    xp_total: int
    level: int
    hearts: int
    current_streak: int
    longest_streak: int
    last_activity_date: date | None
