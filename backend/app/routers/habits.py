"""Habit endpoints: CRUD, daily status and check-off logs."""

from datetime import date

from fastapi import APIRouter, Query, status

from app.core.dependencies import CurrentUser, DbSession
from app.repositories import habit_repository
from app.schemas.habit import (
    HabitCreate,
    HabitLogCreate,
    HabitLogRead,
    HabitRead,
    HabitUpdate,
    HabitWithTodayStatus,
)
from app.services import habit_service

router = APIRouter(prefix="/habits", tags=["Habits"])


@router.post("", response_model=HabitRead, status_code=status.HTTP_201_CREATED)
def create_habit(
    data: HabitCreate, user: CurrentUser, db: DbSession
) -> HabitRead:
    return habit_service.create_habit(db, user.id, data)


@router.get("", response_model=list[HabitRead])
def list_habits(
    user: CurrentUser,
    db: DbSession,
    include_inactive: bool = Query(default=False),
) -> list[HabitRead]:
    return habit_repository.list_habits(db, user.id, include_inactive)


@router.get("/daily", response_model=list[HabitWithTodayStatus])
def daily_status(
    user: CurrentUser,
    db: DbSession,
    for_date: date = Query(default_factory=date.today),
) -> list[HabitWithTodayStatus]:
    """Active habits with their check-off status for a day (default: today)."""
    items = habit_service.habits_with_status(db, user.id, for_date)
    return [
        HabitWithTodayStatus(
            **HabitRead.model_validate(item["habit"]).model_dump(),
            today_log=item["log"],
        )
        for item in items
    ]


@router.put("/{habit_id}", response_model=HabitRead)
def update_habit(
    habit_id: int, data: HabitUpdate, user: CurrentUser, db: DbSession
) -> HabitRead:
    return habit_service.update_habit(db, user.id, habit_id, data)


@router.delete("/{habit_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_habit(habit_id: int, user: CurrentUser, db: DbSession) -> None:
    habit_service.delete_habit(db, user.id, habit_id)


@router.post("/{habit_id}/logs", response_model=HabitLogRead)
def log_habit(
    habit_id: int, data: HabitLogCreate, user: CurrentUser, db: DbSession
) -> HabitLogRead:
    """Check a habit off (or update the check-off) for a day."""
    return habit_service.log_habit(db, user.id, habit_id, data)


@router.get("/{habit_id}/logs", response_model=list[HabitLogRead])
def list_logs(
    habit_id: int,
    user: CurrentUser,
    db: DbSession,
    start_date: date | None = Query(default=None),
    end_date: date | None = Query(default=None),
) -> list[HabitLogRead]:
    return habit_service.list_logs(db, user.id, habit_id, start_date, end_date)
