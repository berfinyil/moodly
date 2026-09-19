"""Achievement catalog: rule-based badges users can unlock."""

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class Achievement(Base):
    """Global achievement catalog. `code` links to a rule function in
    achievement_service — rules live in code, definitions in the database."""

    __tablename__ = "achievements"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(50), unique=True)
    name: Mapped[str] = mapped_column(String(100))
    description: Mapped[str] = mapped_column(String(255))
    emoji: Mapped[str] = mapped_column(String(10))
