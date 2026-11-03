from pydantic import BaseModel, ConfigDict, Field, StringConstraints
from typing import Annotated


class ChapterItem(BaseModel):
    """大纲的一章（也是模型输出的单章结构）。"""
    chapter_id: int = Field(ge=1)
    title: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
    key_points: list[str] = Field(default_factory=list)
    data_needed: list[str] = Field(default_factory=list)
    suggested_words: int = Field(ge=0)


class ChapterOut(ChapterItem):
    model_config = ConfigDict(from_attributes=True)

    id: int


class OutlineOut(BaseModel):
    report_id: int
    target_words: int
    total_words: int
    chapters: list[ChapterOut]


class ChapterUpdate(BaseModel):
    """编辑大纲一章：标题 / 论点 / 所需数据 / 建议字数都可改。"""
    title: str | None = None
    key_points: list[str] | None = None
    data_needed: list[str] | None = None
    suggested_words: int | None = Field(default=None, ge=0)


class ChapterCreate(BaseModel):
    """加一章。"""
    title: str = Field(min_length=1, max_length=512)
    key_points: list[str] = Field(default_factory=list)
    data_needed: list[str] = Field(default_factory=list)
    suggested_words: int = Field(default=0, ge=0)
