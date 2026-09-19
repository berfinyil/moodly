"""Emotion catalog and the many-to-many link to journal entries."""

from sqlalchemy import ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class Emotion(Base):
    """Global catalog of selectable emotions (same for all users)."""

    __tablename__ = "emotions"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50), unique=True)
    emoji: Mapped[str] = mapped_column(String(10))


class JournalEntryEmotion(Base):
    """An emotion selected on a specific journal entry, with intensity 1-5."""

    __tablename__ = "journal_entry_emotions"
    __table_args__ = (
        UniqueConstraint(
            "journal_entry_id", "emotion_id", name="uq_entry_emotion"
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    journal_entry_id: Mapped[int] = mapped_column(
        ForeignKey("journal_entries.id", ondelete="CASCADE"), index=True
    )
    emotion_id: Mapped[int] = mapped_column(
        ForeignKey("emotions.id", ondelete="CASCADE")
    )
    intensity: Mapped[int] = mapped_column(Integer, default=3)  # 1-5

    journal_entry: Mapped["JournalEntry"] = relationship(  # noqa: F821
        back_populates="emotions"
    )
    emotion: Mapped[Emotion] = relationship(lazy="joined")
