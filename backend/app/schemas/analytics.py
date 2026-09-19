"""Pydantic schemas for analytics responses.

All statements are descriptive ("in your documented data") — the service
never produces causal or diagnostic claims.
"""

from datetime import date

from pydantic import BaseModel


class MoodPoint(BaseModel):
    entry_date: date
    mood_score: int | None


class MoodTrend(BaseModel):
    points: list[MoodPoint]
    average: float | None
    average_last_7_days: float | None
    average_last_30_days: float | None


class WeekdayMood(BaseModel):
    weekday: int  # 0 = Montag ... 6 = Sonntag
    weekday_name: str
    average_mood: float
    entry_count: int


class WeekdayAnalytics(BaseModel):
    weekdays: list[WeekdayMood]
    best_weekday: str | None
    worst_weekday: str | None


class SportMoodComparison(BaseModel):
    sport_days: int
    no_sport_days: int
    average_mood_sport_days: float | None
    average_mood_no_sport_days: float | None
    difference: float | None
    statement: str | None


class HabitCompletion(BaseModel):
    habit_id: int
    habit_name: str
    days_tracked: int
    days_completed: int
    completion_rate: float  # 0.0 - 1.0


class EmotionFrequency(BaseModel):
    emotion_id: int
    name: str
    emoji: str
    count: int


class AnalyticsSummary(BaseModel):
    total_entries: int
    entries_last_7_days: int
    average_mood_last_7_days: float | None
    sport_days_last_30_days: int
    data_level: str  # "insufficient" | "basic" | "full"
    data_level_hint: str
