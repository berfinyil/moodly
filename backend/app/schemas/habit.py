"""Pydantic schemas for habits and habit logs."""

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field


class HabitCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    description: str | None = None
    target_value: int | None = Field(default=None, ge=1)
    unit: str | None = Field(default=None, max_length=30)


class HabitUpdate(HabitCreate):
    is_active: bool = True


class HabitRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str | None
    target_value: int | None
    unit: str | None
    is_active: bool
    created_at: datetime


class HabitLogCreate(BaseModel):
    log_date: date
    completed: bool = True
    value: int | None = Field(default=None, ge=0)
    note: str | None = Field(default=None, max_length=500)


class HabitLogRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    habit_id: int
    log_date: date
    completed: bool
    value: int | None
    note: str | None


class HabitWithTodayStatus(HabitRead):
    """Habit plus its log for a given day (for the daily check-off list)."""

    today_log: HabitLogRead | None = None
