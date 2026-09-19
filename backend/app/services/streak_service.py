"""Streak calculation based on journal entry dates."""

from datetime import date, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.journal_entry import JournalEntry


def get_streaks(db: Session, user_id: int) -> dict:
    """Current and longest run of consecutive journal days.

    The current streak counts back from today; if today has no entry yet,
    it counts back from yesterday (today can still be written).
    """
    dates = set(
        db.scalars(
            select(JournalEntry.entry_date).where(
                JournalEntry.user_id == user_id
            )
        )
    )
    if not dates:
        return {"current_streak": 0, "longest_streak": 0}

    # Current streak
    today = date.today()
    anchor = today if today in dates else today - timedelta(days=1)
    current = 0
    day = anchor
    while day in dates:
        current += 1
        day -= timedelta(days=1)

    # Longest streak: walk each run only from its start date
    longest = 0
    for day in dates:
        if day - timedelta(days=1) in dates:
            continue  # not the start of a run
        length = 1
        while day + timedelta(days=length) in dates:
            length += 1
        longest = max(longest, length)

    return {"current_streak": current, "longest_streak": longest}
