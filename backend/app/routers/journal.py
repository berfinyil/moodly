"""Journal entry endpoints. All routes require authentication."""

from datetime import date

from fastapi import APIRouter, Query, status

from app.core.dependencies import CurrentUser, DbSession
from app.repositories import journal_repository
from app.schemas.journal import (
    CalendarDay,
    JournalEntryCreate,
    JournalEntryRead,
    JournalEntryUpdate,
)
from app.services import journal_service

router = APIRouter(prefix="/journal", tags=["Journal"])


@router.post(
    "", response_model=JournalEntryRead, status_code=status.HTTP_201_CREATED
)
def create_entry(
    data: JournalEntryCreate, user: CurrentUser, db: DbSession
) -> JournalEntryRead:
    """Create the journal entry for a day (one entry per day)."""
    return journal_service.create_entry(db, user.id, data)


@router.get("", response_model=list[JournalEntryRead])
def list_entries(
    user: CurrentUser,
    db: DbSession,
    start_date: date | None = Query(default=None),
    end_date: date | None = Query(default=None),
) -> list[JournalEntryRead]:
    """List the user's entries, optionally filtered by date range."""
    return journal_repository.list_entries(db, user.id, start_date, end_date)


@router.get("/calendar", response_model=list[CalendarDay])
def calendar(
    user: CurrentUser,
    db: DbSession,
    start_date: date,
    end_date: date,
) -> list[CalendarDay]:
    """Lightweight day list (date + mood) for the calendar view."""
    entries = journal_repository.list_entries(db, user.id, start_date, end_date)
    return [
        CalendarDay(entry_date=e.entry_date, mood_score=e.mood_score)
        for e in entries
    ]


@router.get("/today", response_model=JournalEntryRead)
def read_today(user: CurrentUser, db: DbSession) -> JournalEntryRead:
    """Return today's entry (404 if none exists yet)."""
    return journal_service.get_entry_by_date(db, user.id, date.today())


@router.get("/date/{entry_date}", response_model=JournalEntryRead)
def read_by_date(
    entry_date: date, user: CurrentUser, db: DbSession
) -> JournalEntryRead:
    """Return the entry for a specific date (YYYY-MM-DD)."""
    return journal_service.get_entry_by_date(db, user.id, entry_date)


@router.get("/{entry_id}", response_model=JournalEntryRead)
def read_entry(
    entry_id: int, user: CurrentUser, db: DbSession
) -> JournalEntryRead:
    return journal_service.get_entry(db, user.id, entry_id)


@router.put("/{entry_id}", response_model=JournalEntryRead)
def update_entry(
    entry_id: int,
    data: JournalEntryUpdate,
    user: CurrentUser,
    db: DbSession,
) -> JournalEntryRead:
    return journal_service.update_entry(db, user.id, entry_id, data)


@router.delete("/{entry_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_entry(entry_id: int, user: CurrentUser, db: DbSession) -> None:
    journal_service.delete_entry(db, user.id, entry_id)
