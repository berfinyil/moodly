"""Pydantic schemas for journal entries."""

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.emotion import EmotionSelection, EntryEmotionRead


class JournalEntryBase(BaseModel):
    """Fields the user can write. All optional except the date."""

    entry_date: date

    mood_score: int | None = Field(default=None, ge=1, le=5)
    energy_level: int | None = Field(default=None, ge=1, le=5)
    stress_level: int | None = Field(default=None, ge=1, le=5)
    sleep_quality: int | None = Field(default=None, ge=1, le=5)
    mood_influence: str | None = None

    did_sport: bool = False
    sport_type: str | None = Field(default=None, max_length=100)
    sport_duration_minutes: int | None = Field(default=None, ge=0)

    had_sex: bool = False
    cried: bool = False

    had_headache: bool = False
    had_pain: bool = False
    pain_level: int | None = Field(default=None, ge=0, le=10)
    pain_location: str | None = Field(default=None, max_length=200)

    notes: str | None = None
    gratitude: str | None = None
    positive_event: str | None = None
    negative_event: str | None = None
    reflection: str | None = None

    emotions: list[EmotionSelection] = []


class JournalEntryCreate(JournalEntryBase):
    pass


class JournalEntryUpdate(JournalEntryBase):
    """Full update — the frontend always sends the whole form."""


class JournalEntryRead(JournalEntryBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    emotions: list[EntryEmotionRead] = []
    created_at: datetime
    updated_at: datetime


class CalendarDay(BaseModel):
    """Lightweight per-day info for the calendar view."""

    entry_date: date
    mood_score: int | None
