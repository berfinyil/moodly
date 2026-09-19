"""Database access for journal entries. All queries are scoped to a user."""

from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.journal_entry import JournalEntry


def get_by_id(db: Session, user_id: int, entry_id: int) -> JournalEntry | None:
    """Return the entry only if it belongs to the given user."""
    entry = db.get(JournalEntry, entry_id)
    if entry is None or entry.user_id != user_id:
        return None
    return entry


def get_by_date(db: Session, user_id: int, entry_date: date) -> JournalEntry | None:
    return db.scalar(
        select(JournalEntry).where(
            JournalEntry.user_id == user_id,
            JournalEntry.entry_date == entry_date,
        )
    )


def list_entries(
    db: Session,
    user_id: int,
    start_date: date | None = None,
    end_date: date | None = None,
) -> list[JournalEntry]:
    query = select(JournalEntry).where(JournalEntry.user_id == user_id)
    if start_date is not None:
        query = query.where(JournalEntry.entry_date >= start_date)
    if end_date is not None:
        query = query.where(JournalEntry.entry_date <= end_date)
    query = query.order_by(JournalEntry.entry_date.desc())
    return list(db.scalars(query))


def delete(db: Session, entry: JournalEntry) -> None:
    db.delete(entry)
    db.commit()
