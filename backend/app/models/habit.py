"""Habit model: a recurring habit the user wants to track."""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class Habit(Base):
    __tablename__ = "habits"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    name: Mapped[str] = mapped_column(String(100))
    description: Mapped[str | None] = mapped_column(Text)
    # Optional numeric target, e.g. "Lesen: 20 Minuten" -> target_value=20
    target_value: Mapped[int | None] = mapped_column()
    unit: Mapped[str | None] = mapped_column(String(30))  # e.g. "Minuten"
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )

    logs: Mapped[list["HabitLog"]] = relationship(  # noqa: F821
        back_populates="habit", cascade="all, delete-orphan"
    )
