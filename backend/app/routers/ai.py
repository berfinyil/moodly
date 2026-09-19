"""AI endpoints: daily reflection question and weekly summary."""

from fastapi import APIRouter

from app.core.dependencies import CurrentUser, DbSession
from app.schemas.ai import DailyQuestion, WeeklySummary
from app.services import ai_service

router = APIRouter(prefix="/ai", tags=["AI"])


@router.get("/daily-question", response_model=DailyQuestion)
def daily_question(user: CurrentUser) -> DailyQuestion:
    """Today's reflection question (deterministic, no external API)."""
    return ai_service.get_daily_question()


@router.post("/weekly-summary", response_model=WeeklySummary)
def weekly_summary(user: CurrentUser, db: DbSession) -> WeeklySummary:
    """Generate the summary for the current week.

    Numbers are computed by the backend; a language model (if configured)
    only rephrases them. Sensitive fields never enter the prompt.
    """
    return ai_service.generate_weekly_summary(db, user.id)
