"""Pydantic schemas for achievements and streaks."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class AchievementRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    name: str
    description: str
    emoji: str


class AchievementStatus(BaseModel):
    achievement: AchievementRead
    unlocked_at: datetime | None


class StreakRead(BaseModel):
    current_streak: int
    longest_streak: int
