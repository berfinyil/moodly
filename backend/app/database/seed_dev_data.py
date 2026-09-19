"""Development seed script: creates ~90 days of clearly marked test data.

Usage (from backend/):
    .venv/bin/python -m app.database.seed_dev_data <email>

All generated notes start with "[Testdaten]" so they are recognizable.
Existing entries for a day are skipped, nothing is overwritten.
"""

import random
import sys
from datetime import date, timedelta

from sqlalchemy import select

from app.database.database import SessionLocal
from app.models.emotion import Emotion, JournalEntryEmotion
from app.models.habit import Habit
from app.models.habit_log import HabitLog
from app.models.journal_entry import JournalEntry
from app.models.user import User
from app.repositories import journal_repository

SPORT_TYPES = ["Fitness", "Yoga", "Laufen", "Schwimmen", "Radfahren"]


def seed(email: str, days: int = 90) -> None:
    random.seed(42)  # reproducible test data
    db = SessionLocal()
    try:
        user = db.scalar(select(User).where(User.email == email))
        if user is None:
            print(f"Kein Benutzer mit E-Mail {email} gefunden.")
            sys.exit(1)

        emotion_ids = list(db.scalars(select(Emotion.id)))

        # One demo habit if the user has none yet
        habit = db.scalar(select(Habit).where(Habit.user_id == user.id))
        if habit is None:
            habit = Habit(user_id=user.id, name="Lesen (Testdaten)", target_value=20, unit="Minuten")
            db.add(habit)
            db.flush()

        created = 0
        today = date.today()
        for offset in range(1, days + 1):
            entry_date = today - timedelta(days=offset)
            if journal_repository.get_by_date(db, user.id, entry_date):
                continue  # never overwrite real entries

            # Weekend days trend slightly happier, sport lifts mood a bit
            base_mood = 3.4 if entry_date.weekday() >= 5 else 2.9
            did_sport = random.random() < 0.4
            mood = round(
                min(5, max(1, random.gauss(base_mood + (0.6 if did_sport else 0), 0.9)))
            )

            entry = JournalEntry(
                user_id=user.id,
                entry_date=entry_date,
                mood_score=mood,
                energy_level=random.randint(1, 5),
                stress_level=random.randint(1, 5),
                sleep_quality=random.randint(1, 5),
                did_sport=did_sport,
                sport_type=random.choice(SPORT_TYPES) if did_sport else None,
                sport_duration_minutes=random.choice([30, 45, 60, 90]) if did_sport else None,
                cried=random.random() < 0.08,
                had_headache=random.random() < 0.15,
                notes="[Testdaten] Automatisch generierter Eintrag.",
            )
            for emotion_id in random.sample(emotion_ids, k=random.randint(1, 3)):
                entry.emotions.append(
                    JournalEntryEmotion(emotion_id=emotion_id, intensity=random.randint(1, 5))
                )
            db.add(entry)

            if random.random() < 0.7:
                db.add(
                    HabitLog(
                        habit_id=habit.id,
                        log_date=entry_date,
                        completed=random.random() < 0.8,
                        value=random.choice([10, 15, 20, 25, 30]),
                    )
                )
            created += 1

        db.commit()
        print(f"{created} Test-Journaleinträge für {email} angelegt.")
    finally:
        db.close()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python -m app.database.seed_dev_data <email>")
        sys.exit(1)
    seed(sys.argv[1])
