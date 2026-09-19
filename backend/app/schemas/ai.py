"""Pydantic schemas for AI endpoints."""

from datetime import date

from pydantic import BaseModel


class DailyQuestion(BaseModel):
    question: str


class WeeklySummaryFacts(BaseModel):
    week_start: date
    week_end: date
    days_written: int
    average_mood: float | None
    average_stress: float | None
    sport_days: int
    top_emotions: list[str]
    current_streak: int


class WeeklySummary(BaseModel):
    week_start: date
    week_end: date
    summary: str
    facts: WeeklySummaryFacts
