"""Statistical analytics computed with pandas.

This module only computes numbers from documented data. Any natural-language
framing stays descriptive (correlation, never causation) and the AI layer
(later) may rephrase but never invent numbers.
"""

from datetime import date, timedelta

import pandas as pd
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.emotion import Emotion, JournalEntryEmotion
from app.models.journal_entry import JournalEntry
from app.repositories import habit_repository

WEEKDAY_NAMES = [
    "Montag",
    "Dienstag",
    "Mittwoch",
    "Donnerstag",
    "Freitag",
    "Samstag",
    "Sonntag",
]

# Minimum amounts of data before we show statistics
MIN_ENTRIES_BASIC = 7
MIN_ENTRIES_FULL = 30
MIN_DAYS_PER_GROUP = 3  # e.g. at least 3 sport days AND 3 non-sport days


def _entries_dataframe(db: Session, user_id: int) -> pd.DataFrame:
    """All journal entries of a user as a pandas DataFrame."""
    rows = db.execute(
        select(
            JournalEntry.entry_date,
            JournalEntry.mood_score,
            JournalEntry.did_sport,
        ).where(JournalEntry.user_id == user_id)
    ).all()
    df = pd.DataFrame(rows, columns=["entry_date", "mood_score", "did_sport"])
    if not df.empty:
        df["entry_date"] = pd.to_datetime(df["entry_date"])
    return df


def _round(value: float | None) -> float | None:
    return None if value is None or pd.isna(value) else round(float(value), 2)


def summary(db: Session, user_id: int) -> dict:
    df = _entries_dataframe(db, user_id)
    today = pd.Timestamp(date.today())

    total = len(df)
    if total < MIN_ENTRIES_BASIC:
        level, hint = (
            "insufficient",
            "Noch nicht genügend Daten für eine zuverlässige Auswertung. "
            f"Schreibe mindestens {MIN_ENTRIES_BASIC} Tage, um erste Trends zu sehen.",
        )
    elif total < MIN_ENTRIES_FULL:
        level, hint = ("basic", "Erste Trends verfügbar. Ab 30 Einträgen gibt es umfangreichere Statistiken.")
    else:
        level, hint = ("full", "Umfangreiche Statistiken verfügbar.")

    last7 = df[df["entry_date"] >= today - pd.Timedelta(days=6)] if not df.empty else df
    last30 = df[df["entry_date"] >= today - pd.Timedelta(days=29)] if not df.empty else df

    return {
        "total_entries": total,
        "entries_last_7_days": len(last7),
        "average_mood_last_7_days": _round(last7["mood_score"].mean()) if not last7.empty else None,
        "sport_days_last_30_days": int(last30["did_sport"].sum()) if not last30.empty else 0,
        "data_level": level,
        "data_level_hint": hint,
    }


def mood_trend(db: Session, user_id: int, days: int = 30) -> dict:
    df = _entries_dataframe(db, user_id)
    today = pd.Timestamp(date.today())
    start = today - pd.Timedelta(days=days - 1)

    window = df[df["entry_date"] >= start].sort_values("entry_date") if not df.empty else df
    last7 = df[df["entry_date"] >= today - pd.Timedelta(days=6)] if not df.empty else df
    last30 = df[df["entry_date"] >= today - pd.Timedelta(days=29)] if not df.empty else df

    return {
        "points": [
            {
                "entry_date": row.entry_date.date(),
                "mood_score": None if pd.isna(row.mood_score) else int(row.mood_score),
            }
            for row in window.itertuples()
        ],
        "average": _round(df["mood_score"].mean()) if not df.empty else None,
        "average_last_7_days": _round(last7["mood_score"].mean()) if not last7.empty else None,
        "average_last_30_days": _round(last30["mood_score"].mean()) if not last30.empty else None,
    }


def weekday_mood(db: Session, user_id: int) -> dict:
    df = _entries_dataframe(db, user_id)
    df = df.dropna(subset=["mood_score"]) if not df.empty else df

    if df.empty or len(df) < MIN_ENTRIES_BASIC:
        return {"weekdays": [], "best_weekday": None, "worst_weekday": None}

    df = df.assign(weekday=df["entry_date"].dt.dayofweek)
    grouped = df.groupby("weekday")["mood_score"].agg(["mean", "count"])

    weekdays = [
        {
            "weekday": int(day),
            "weekday_name": WEEKDAY_NAMES[int(day)],
            "average_mood": _round(row["mean"]),
            "entry_count": int(row["count"]),
        }
        for day, row in grouped.iterrows()
    ]

    # Best/worst only over weekdays with enough data points
    reliable = grouped[grouped["count"] >= MIN_DAYS_PER_GROUP]
    best = WEEKDAY_NAMES[int(reliable["mean"].idxmax())] if not reliable.empty else None
    worst = WEEKDAY_NAMES[int(reliable["mean"].idxmin())] if not reliable.empty else None

    return {"weekdays": weekdays, "best_weekday": best, "worst_weekday": worst}


def sport_vs_mood(db: Session, user_id: int) -> dict:
    df = _entries_dataframe(db, user_id)
    df = df.dropna(subset=["mood_score"]) if not df.empty else df

    sport = df[df["did_sport"]] if not df.empty else df
    no_sport = df[~df["did_sport"]] if not df.empty else df

    result = {
        "sport_days": len(sport),
        "no_sport_days": len(no_sport),
        "average_mood_sport_days": _round(sport["mood_score"].mean()) if not sport.empty else None,
        "average_mood_no_sport_days": _round(no_sport["mood_score"].mean()) if not no_sport.empty else None,
        "difference": None,
        "statement": None,
    }

    # Only make a statement when both groups have enough days
    if len(sport) >= MIN_DAYS_PER_GROUP and len(no_sport) >= MIN_DAYS_PER_GROUP:
        diff = _round(sport["mood_score"].mean() - no_sport["mood_score"].mean())
        result["difference"] = diff
        direction = "höher" if diff > 0 else "niedriger"
        diff_german = f"{abs(diff):.1f}".replace(".", ",")
        result["statement"] = (
            "An Tagen, an denen du Sport dokumentiert hast, war deine "
            f"durchschnittliche Stimmung um {diff_german} Punkte {direction}."
            if diff != 0
            else "Deine durchschnittliche Stimmung war an Sporttagen und Tagen ohne Sport etwa gleich."
        )
    else:
        result["statement"] = "Noch nicht genügend Daten für eine zuverlässige Auswertung."

    return result


def habit_completion(db: Session, user_id: int, days: int = 30) -> list[dict]:
    """Completion rate per active habit over the last `days` days."""
    end = date.today()
    start = end - timedelta(days=days - 1)
    result = []
    for habit in habit_repository.list_habits(db, user_id):
        logs = habit_repository.list_logs(db, habit.id, start, end)
        completed = sum(1 for log in logs if log.completed)
        result.append(
            {
                "habit_id": habit.id,
                "habit_name": habit.name,
                "days_tracked": len(logs),
                "days_completed": completed,
                "completion_rate": round(completed / days, 2),
            }
        )
    return result


def emotion_frequencies(db: Session, user_id: int, days: int = 30) -> list[dict]:
    """How often each emotion was selected in the last `days` days."""
    start = date.today() - timedelta(days=days - 1)
    rows = db.execute(
        select(Emotion.id, Emotion.name, Emotion.emoji, JournalEntryEmotion.id)
        .join(JournalEntryEmotion, JournalEntryEmotion.emotion_id == Emotion.id)
        .join(JournalEntry, JournalEntry.id == JournalEntryEmotion.journal_entry_id)
        .where(
            JournalEntry.user_id == user_id,
            JournalEntry.entry_date >= start,
        )
    ).all()

    df = pd.DataFrame(rows, columns=["emotion_id", "name", "emoji", "link_id"])
    if df.empty:
        return []
    grouped = (
        df.groupby(["emotion_id", "name", "emoji"])
        .size()
        .reset_index(name="count")
        .sort_values("count", ascending=False)
    )
    return [
        {
            "emotion_id": int(row.emotion_id),
            "name": row.name,
            "emoji": row.emoji,
            "count": int(row.count),
        }
        for row in grouped.itertuples()
    ]
