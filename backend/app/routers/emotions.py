"""Emotion catalog endpoint."""

from sqlalchemy import select

from fastapi import APIRouter

from app.core.dependencies import CurrentUser, DbSession
from app.models.emotion import Emotion
from app.schemas.emotion import EmotionRead

router = APIRouter(prefix="/emotions", tags=["Emotions"])


@router.get("", response_model=list[EmotionRead])
def list_emotions(user: CurrentUser, db: DbSession) -> list[EmotionRead]:
    """Return all selectable emotions."""
    return list(db.scalars(select(Emotion).order_by(Emotion.id)))
