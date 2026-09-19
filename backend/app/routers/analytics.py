"""Analytics endpoints. All numbers are computed in analytics_service."""

from fastapi import APIRouter, Query

from app.core.dependencies import CurrentUser, DbSession
from app.schemas.analytics import (
    AnalyticsSummary,
    EmotionFrequency,
    HabitCompletion,
    MoodTrend,
    SportMoodComparison,
    WeekdayAnalytics,
)
from app.services import analytics_service

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/summary", response_model=AnalyticsSummary)
def summary(user: CurrentUser, db: DbSession) -> AnalyticsSummary:
    """Overview: entry counts, recent mood average and data level."""
    return analytics_service.summary(db, user.id)


@router.get("/mood", response_model=MoodTrend)
def mood(
    user: CurrentUser,
    db: DbSession,
    days: int = Query(default=30, ge=7, le=365),
) -> MoodTrend:
    """Mood time series for the last `days` days plus averages."""
    return analytics_service.mood_trend(db, user.id, days)


@router.get("/weekday", response_model=WeekdayAnalytics)
def weekday(user: CurrentUser, db: DbSession) -> WeekdayAnalytics:
    """Average mood per weekday (empty until enough data exists)."""
    return analytics_service.weekday_mood(db, user.id)


@router.get("/sport", response_model=SportMoodComparison)
def sport(user: CurrentUser, db: DbSession) -> SportMoodComparison:
    """Average mood on sport days vs. days without sport (correlation only)."""
    return analytics_service.sport_vs_mood(db, user.id)


@router.get("/habits", response_model=list[HabitCompletion])
def habits(
    user: CurrentUser,
    db: DbSession,
    days: int = Query(default=30, ge=7, le=365),
) -> list[HabitCompletion]:
    """Completion rate per active habit over the last `days` days."""
    return analytics_service.habit_completion(db, user.id, days)


@router.get("/emotions", response_model=list[EmotionFrequency])
def emotions(
    user: CurrentUser,
    db: DbSession,
    days: int = Query(default=30, ge=7, le=365),
) -> list[EmotionFrequency]:
    """Most frequently selected emotions in the last `days` days."""
    return analytics_service.emotion_frequencies(db, user.id, days)
