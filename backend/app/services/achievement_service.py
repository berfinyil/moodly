"""Rule-based achievement system.

Definitions (name, description, emoji) live in the achievements table;
the unlock rules live here as small functions keyed by achievement code.
`check_achievements` is called after relevant actions (e.g. saving a
journal entry) and unlocks anything newly earned — idempotent, so calling
it twice never duplicates an unlock.
"""

from collections.abc import Callable

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.achievement import Achievement
from app.models.habit_log import HabitLog
from app.models.habit import Habit
from app.models.journal_entry import JournalEntry
from app.models.user_achievement import UserAchievement
from app.services import streak_service

DEFAULT_ACHIEVEMENTS: list[dict] = [
    {"code": "first_entry", "name": "Erster Schritt", "description": "Ersten Journaleintrag erstellt", "emoji": "🌱"},
    {"code": "week_streak", "name": "Eine Woche", "description": "7 Tage Journaling am Stück", "emoji": "📅"},
    {"code": "entries_30", "name": "Dranbleiber", "description": "30 Journaleinträge geschrieben", "emoji": "✍️"},
    {"code": "entries_100", "name": "100 Club", "description": "100 Journaleinträge geschrieben", "emoji": "💯"},
    {"code": "sport_10", "name": "Sportlich", "description": "10 Sporttage dokumentiert", "emoji": "🏃"},
    {"code": "reflective_10", "name": "Reflektiert", "description": "10 Tagesreflexionen geschrieben", "emoji": "🪞"},
    {"code": "habit_30_logs", "name": "Gewohnheitstier", "description": "Einen Habit an 30 Tagen getrackt", "emoji": "🔁"},
    {"code": "streak_30", "name": "Monatsmeister", "description": "30 Tage Journaling am Stück", "emoji": "🔥"},
]


def seed_achievements(db: Session) -> None:
    """Insert missing achievement definitions (idempotent)."""
    existing = set(db.scalars(select(Achievement.code)))
    for data in DEFAULT_ACHIEVEMENTS:
        if data["code"] not in existing:
            db.add(Achievement(**data))
    db.commit()


# ---------- Rules: code -> function(db, user_id) -> bool ----------

def _entry_count(db: Session, user_id: int) -> int:
    return db.scalar(
        select(func.count(JournalEntry.id)).where(JournalEntry.user_id == user_id)
    )


def _rule_first_entry(db: Session, user_id: int) -> bool:
    return _entry_count(db, user_id) >= 1


def _rule_entries_30(db: Session, user_id: int) -> bool:
    return _entry_count(db, user_id) >= 30


def _rule_entries_100(db: Session, user_id: int) -> bool:
    return _entry_count(db, user_id) >= 100


def _rule_week_streak(db: Session, user_id: int) -> bool:
    return streak_service.get_streaks(db, user_id)["longest_streak"] >= 7


def _rule_streak_30(db: Session, user_id: int) -> bool:
    return streak_service.get_streaks(db, user_id)["longest_streak"] >= 30


def _rule_sport_10(db: Session, user_id: int) -> bool:
    count = db.scalar(
        select(func.count(JournalEntry.id)).where(
            JournalEntry.user_id == user_id,
            JournalEntry.did_sport.is_(True),
        )
    )
    return count >= 10


def _rule_reflective_10(db: Session, user_id: int) -> bool:
    count = db.scalar(
        select(func.count(JournalEntry.id)).where(
            JournalEntry.user_id == user_id,
            JournalEntry.reflection.is_not(None),
            JournalEntry.reflection != "",
        )
    )
    return count >= 10


def _rule_habit_30_logs(db: Session, user_id: int) -> bool:
    count = db.scalar(
        select(func.count(HabitLog.id))
        .join(Habit, Habit.id == HabitLog.habit_id)
        .where(Habit.user_id == user_id)
        .group_by(HabitLog.habit_id)
        .order_by(func.count(HabitLog.id).desc())
        .limit(1)
    )
    return (count or 0) >= 30


RULES: dict[str, Callable[[Session, int], bool]] = {
    "first_entry": _rule_first_entry,
    "week_streak": _rule_week_streak,
    "entries_30": _rule_entries_30,
    "entries_100": _rule_entries_100,
    "sport_10": _rule_sport_10,
    "reflective_10": _rule_reflective_10,
    "habit_30_logs": _rule_habit_30_logs,
    "streak_30": _rule_streak_30,
}


# ---------- Checking & querying ----------

def check_achievements(db: Session, user_id: int) -> list[Achievement]:
    """Evaluate all rules and unlock newly earned achievements.

    Returns the list of achievements unlocked by this call.
    """
    unlocked_ids = set(
        db.scalars(
            select(UserAchievement.achievement_id).where(
                UserAchievement.user_id == user_id
            )
        )
    )
    newly_unlocked = []
    for achievement in db.scalars(select(Achievement)):
        if achievement.id in unlocked_ids:
            continue
        rule = RULES.get(achievement.code)
        if rule is not None and rule(db, user_id):
            db.add(
                UserAchievement(user_id=user_id, achievement_id=achievement.id)
            )
            newly_unlocked.append(achievement)
    if newly_unlocked:
        db.commit()
    return newly_unlocked


def list_achievements(db: Session, user_id: int) -> list[dict]:
    """All achievements with unlock status for the user."""
    unlocked = {
        ua.achievement_id: ua.unlocked_at
        for ua in db.scalars(
            select(UserAchievement).where(UserAchievement.user_id == user_id)
        )
    }
    return [
        {
            "achievement": achievement,
            "unlocked_at": unlocked.get(achievement.id),
        }
        for achievement in db.scalars(select(Achievement).order_by(Achievement.id))
    ]
