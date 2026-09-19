"""Seed data for the global emotion catalog."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.emotion import Emotion

DEFAULT_EMOTIONS: list[dict] = [
    {"name": "glücklich", "emoji": "😄"},
    {"name": "traurig", "emoji": "😢"},
    {"name": "gestresst", "emoji": "😫"},
    {"name": "entspannt", "emoji": "😌"},
    {"name": "motiviert", "emoji": "💪"},
    {"name": "müde", "emoji": "😴"},
    {"name": "wütend", "emoji": "😠"},
    {"name": "ängstlich", "emoji": "😰"},
    {"name": "dankbar", "emoji": "🙏"},
    {"name": "einsam", "emoji": "🫥"},
    {"name": "zufrieden", "emoji": "🙂"},
    {"name": "überfordert", "emoji": "🤯"},
    {"name": "verliebt", "emoji": "😍"},
    {"name": "gelangweilt", "emoji": "🥱"},
]


def seed_emotions(db: Session) -> None:
    """Insert any default emotions that don't exist yet (idempotent)."""
    existing = set(db.scalars(select(Emotion.name)))
    for data in DEFAULT_EMOTIONS:
        if data["name"] not in existing:
            db.add(Emotion(**data))
    db.commit()
