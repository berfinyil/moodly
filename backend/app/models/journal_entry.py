"""Journal entry model: one central entry per user per day."""

from datetime import date, datetime

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class JournalEntry(Base):
    __tablename__ = "journal_entries"
    __table_args__ = (
        # One main entry per user per day
        UniqueConstraint("user_id", "entry_date", name="uq_journal_user_date"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    entry_date: Mapped[date] = mapped_column(Date, index=True)

    # Wellbeing scales (1-5)
    mood_score: Mapped[int | None] = mapped_column(Integer)
    energy_level: Mapped[int | None] = mapped_column(Integer)
    stress_level: Mapped[int | None] = mapped_column(Integer)
    sleep_quality: Mapped[int | None] = mapped_column(Integer)
    mood_influence: Mapped[str | None] = mapped_column(Text)

    # Sport
    did_sport: Mapped[bool] = mapped_column(Boolean, default=False)
    sport_type: Mapped[str | None] = mapped_column(String(100))
    sport_duration_minutes: Mapped[int | None] = mapped_column(Integer)

    # Very private flags
    had_sex: Mapped[bool] = mapped_column(Boolean, default=False)
    cried: Mapped[bool] = mapped_column(Boolean, default=False)

    # Pain
    had_headache: Mapped[bool] = mapped_column(Boolean, default=False)
    had_pain: Mapped[bool] = mapped_column(Boolean, default=False)
    pain_level: Mapped[int | None] = mapped_column(Integer)  # 0-10
    pain_location: Mapped[str | None] = mapped_column(String(200))

    # Free text / reflection
    notes: Mapped[str | None] = mapped_column(Text)
    gratitude: Mapped[str | None] = mapped_column(Text)
    positive_event: Mapped[str | None] = mapped_column(Text)
    negative_event: Mapped[str | None] = mapped_column(Text)
    reflection: Mapped[str | None] = mapped_column(Text)

    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    emotions: Mapped[list["JournalEntryEmotion"]] = relationship(
        back_populates="journal_entry", cascade="all, delete-orphan"
    )
