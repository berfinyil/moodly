"""Business logic for journal entries."""

from datetime import date

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.emotion import Emotion, JournalEntryEmotion
from app.models.journal_entry import JournalEntry
from app.repositories import journal_repository
from app.schemas.emotion import EmotionSelection
from app.services import achievement_service
from app.schemas.journal import JournalEntryCreate, JournalEntryUpdate

_ENTRY_FIELDS = [
    "entry_date",
    "mood_score",
    "energy_level",
    "stress_level",
    "sleep_quality",
    "mood_influence",
    "did_sport",
    "sport_type",
    "sport_duration_minutes",
    "had_sex",
    "cried",
    "had_headache",
    "had_pain",
    "pain_level",
    "pain_location",
    "notes",
    "gratitude",
    "positive_event",
    "negative_event",
    "reflection",
]


def _not_found() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Journaleintrag nicht gefunden.",
    )


def _validate_emotion_ids(db: Session, selections: list[EmotionSelection]) -> None:
    if not selections:
        return
    ids = {s.emotion_id for s in selections}
    if len(ids) != len(selections):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Jede Emotion darf pro Tag nur einmal ausgewählt werden.",
        )
    existing = set(db.scalars(select(Emotion.id).where(Emotion.id.in_(ids))))
    missing = ids - existing
    if missing:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Unbekannte Emotion ausgewählt.",
        )


def _set_emotions(
    entry: JournalEntry, selections: list[EmotionSelection]
) -> None:
    """Replace the entry's emotions with the given selection."""
    entry.emotions = [
        JournalEntryEmotion(emotion_id=s.emotion_id, intensity=s.intensity)
        for s in selections
    ]


def create_entry(
    db: Session, user_id: int, data: JournalEntryCreate
) -> JournalEntry:
    if journal_repository.get_by_date(db, user_id, data.entry_date):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Für diesen Tag existiert bereits ein Eintrag.",
        )
    _validate_emotion_ids(db, data.emotions)

    entry = JournalEntry(
        user_id=user_id,
        **{field: getattr(data, field) for field in _ENTRY_FIELDS},
    )
    _set_emotions(entry, data.emotions)
    db.add(entry)
    db.commit()
    db.refresh(entry)
    achievement_service.check_achievements(db, user_id)
    return entry


def update_entry(
    db: Session, user_id: int, entry_id: int, data: JournalEntryUpdate
) -> JournalEntry:
    entry = journal_repository.get_by_id(db, user_id, entry_id)
    if entry is None:
        raise _not_found()

    # Prevent moving the entry onto a date that already has another entry
    other = journal_repository.get_by_date(db, user_id, data.entry_date)
    if other is not None and other.id != entry.id:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Für diesen Tag existiert bereits ein Eintrag.",
        )
    _validate_emotion_ids(db, data.emotions)

    for field in _ENTRY_FIELDS:
        setattr(entry, field, getattr(data, field))

    # Delete the old emotion rows first, otherwise the unique constraint
    # (entry_id, emotion_id) fires when an emotion is kept across the update.
    entry.emotions.clear()
    db.flush()
    _set_emotions(entry, data.emotions)

    db.commit()
    db.refresh(entry)
    achievement_service.check_achievements(db, user_id)
    return entry


def get_entry(db: Session, user_id: int, entry_id: int) -> JournalEntry:
    entry = journal_repository.get_by_id(db, user_id, entry_id)
    if entry is None:
        raise _not_found()
    return entry


def get_entry_by_date(
    db: Session, user_id: int, entry_date: date
) -> JournalEntry:
    entry = journal_repository.get_by_date(db, user_id, entry_date)
    if entry is None:
        raise _not_found()
    return entry


def delete_entry(db: Session, user_id: int, entry_id: int) -> None:
    entry = journal_repository.get_by_id(db, user_id, entry_id)
    if entry is None:
        raise _not_found()
    journal_repository.delete(db, entry)
