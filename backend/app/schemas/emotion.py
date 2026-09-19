"""Pydantic schemas for emotions."""

from pydantic import BaseModel, ConfigDict, Field


class EmotionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    emoji: str


class EmotionSelection(BaseModel):
    """An emotion the user picks for a day, with intensity 1-5."""

    emotion_id: int
    intensity: int = Field(default=3, ge=1, le=5)


class EntryEmotionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    emotion_id: int
    intensity: int
    emotion: EmotionRead
