"""Business logic for habits and daily check-offs."""

from datetime import date

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.habit import Habit
from app.models.habit_log import HabitLog
from app.repositories import habit_repository
from app.schemas.habit import HabitCreate, HabitLogCreate, HabitUpdate
from app.services import achievement_service


def _not_found() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Habit nicht gefunden.",
    )


def create_habit(db: Session, user_id: int, data: HabitCreate) -> Habit:
    habit = Habit(user_id=user_id, **data.model_dump())
    db.add(habit)
    db.commit()
    db.refresh(habit)
    return habit


def update_habit(
    db: Session, user_id: int, habit_id: int, data: HabitUpdate
) -> Habit:
    habit = habit_repository.get_by_id(db, user_id, habit_id)
    if habit is None:
        raise _not_found()
    for field, value in data.model_dump().items():
        setattr(habit, field, value)
    db.commit()
    db.refresh(habit)
    return habit


def delete_habit(db: Session, user_id: int, habit_id: int) -> None:
    habit = habit_repository.get_by_id(db, user_id, habit_id)
    if habit is None:
        raise _not_found()
    db.delete(habit)
    db.commit()


def log_habit(
    db: Session, user_id: int, habit_id: int, data: HabitLogCreate
) -> HabitLog:
    """Create or update the log for a day (upsert per habit + date)."""
    habit = habit_repository.get_by_id(db, user_id, habit_id)
    if habit is None:
        raise _not_found()

    log = habit_repository.get_log(db, habit_id, data.log_date)
    if log is None:
        log = HabitLog(habit_id=habit_id, **data.model_dump())
        db.add(log)
    else:
        log.completed = data.completed
        log.value = data.value
        log.note = data.note
    db.commit()
    db.refresh(log)
    achievement_service.check_achievements(db, user_id)
    return log


def list_logs(
    db: Session,
    user_id: int,
    habit_id: int,
    start_date: date | None,
    end_date: date | None,
) -> list[HabitLog]:
    habit = habit_repository.get_by_id(db, user_id, habit_id)
    if habit is None:
        raise _not_found()
    return habit_repository.list_logs(db, habit_id, start_date, end_date)


def habits_with_status(
    db: Session, user_id: int, for_date: date
) -> list[dict]:
    """Active habits plus their log for the given day (for daily check-off)."""
    result = []
    for habit in habit_repository.list_habits(db, user_id):
        log = habit_repository.get_log(db, habit.id, for_date)
        result.append({"habit": habit, "log": log})
    return result
