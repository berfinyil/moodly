"""Achievement and streak endpoints."""

from fastapi import APIRouter

from app.core.dependencies import CurrentUser, DbSession
from app.schemas.achievement import AchievementStatus, StreakRead
from app.services import achievement_service, streak_service

router = APIRouter(tags=["Achievements"])


@router.get("/achievements", response_model=list[AchievementStatus])
def list_achievements(user: CurrentUser, db: DbSession) -> list[AchievementStatus]:
    """All achievements with the user's unlock status."""
    return achievement_service.list_achievements(db, user.id)


@router.get("/streak", response_model=StreakRead)
def get_streak(user: CurrentUser, db: DbSession) -> StreakRead:
    """Current and longest journaling streak."""
    return streak_service.get_streaks(db, user.id)
