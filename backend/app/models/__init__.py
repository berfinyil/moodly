"""Import all models here so Base.metadata knows about every table.

Alembic autogenerate and create_all rely on this.
"""

from app.models.achievement import Achievement
from app.models.emotion import Emotion, JournalEntryEmotion
from app.models.habit import Habit
from app.models.habit_log import HabitLog
from app.models.journal_entry import JournalEntry
from app.models.user import User
from app.models.user_achievement import UserAchievement

__all__ = [
    "Achievement",
    "UserAchievement",
    "User",
    "JournalEntry",
    "Emotion",
    "JournalEntryEmotion",
    "Habit",
    "HabitLog",
]
