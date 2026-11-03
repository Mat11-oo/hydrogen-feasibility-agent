from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.core.config import settings


class ReportCreate(BaseModel):
    title: str = Field(min_length=1, max_length=512)
    target_words: int = Field(default=settings.TARGET_WORDS_DEFAULT, ge=1, le=settings.TARGET_WORDS_MAX)
    user_requirements: str = Field(default="", max_length=2000)


class ReportOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    target_words: int
    user_requirements: str
    status: str
    created_at: datetime
