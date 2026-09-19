"""Database access for habits and habit logs. All queries scoped to a user."""

from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.habit import Habit
from app.models.habit_log import HabitLog


def get_by_id(db: Session, user_id: int, habit_id: int) -> Habit | None:
    habit = db.get(Habit, habit_id)
    if habit is None or habit.user_id != user_id:
        return None
    return habit


def list_habits(
    db: Session, user_id: int, include_inactive: bool = False
) -> list[Habit]:
    query = select(Habit).where(Habit.user_id == user_id)
    if not include_inactive:
        query = query.where(Habit.is_active.is_(True))
    return list(db.scalars(query.order_by(Habit.created_at)))


def get_log(db: Session, habit_id: int, log_date: date) -> HabitLog | None:
    return db.scalar(
        select(HabitLog).where(
            HabitLog.habit_id == habit_id,
            HabitLog.log_date == log_date,
        )
    )


def list_logs(
    db: Session,
    habit_id: int,
    start_date: date | None = None,
    end_date: date | None = None,
) -> list[HabitLog]:
    query = select(HabitLog).where(HabitLog.habit_id == habit_id)
    if start_date is not None:
        query = query.where(HabitLog.log_date >= start_date)
    if end_date is not None:
        query = query.where(HabitLog.log_date <= end_date)
    return list(db.scalars(query.order_by(HabitLog.log_date.desc())))
