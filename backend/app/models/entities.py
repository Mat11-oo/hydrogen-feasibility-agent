"""数据库实体。阶段 2-1 只建当前阶段确认要用的字段和状态，后续阶段增量加。"""
import datetime
import enum

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.config import settings
from app.core.database import Base


class DocumentStatus(str, enum.Enum):
    """资料解析状态：可用 / 无文字 / 失败。"""
    AVAILABLE = "available"       # 可用（切成 N 段）
    NO_TEXT = "no_text"           # 无文字，检索不到（扫描件等）
    FAILED = "failed"             # 失败：原因


class ReportStatus(str, enum.Enum):
    """报告状态。阶段 2-1 只用「待确认大纲」，其余状态阶段 2-2 再加。"""
    OUTLINE_PENDING = "outline_pending"  # 待确认大纲


def _now() -> datetime.datetime:
    return datetime.datetime.now(datetime.timezone.utc)


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    owner_id: Mapped[str] = mapped_column(String(64), default=settings.DEFAULT_OWNER, index=True)
    filename: Mapped[str] = mapped_column(String(512))          # 安全化后的存储文件名
    original_name: Mapped[str] = mapped_column(String(512))     # 用户原始文件名（展示用）
    file_type: Mapped[str] = mapped_column(String(16))          # pdf / docx / md / txt
    status: Mapped[str] = mapped_column(String(16), default=DocumentStatus.AVAILABLE.value)
    error_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    chunk_count: Mapped[int] = mapped_column(Integer, default=0)
    stored_path: Mapped[str] = mapped_column(String(1024))      # 本地文件路径
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), default=_now)

    chunks: Mapped[list["DocumentChunk"]] = relationship(back_populates="document", cascade="all, delete-orphan")


class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    document_id: Mapped[int] = mapped_column(ForeignKey("documents.id"), index=True)
    chunk_index: Mapped[int] = mapped_column(Integer)           # 从 0 开始
    content: Mapped[str] = mapped_column(Text)

    document: Mapped["Document"] = relationship(back_populates="chunks")


class Report(Base):
    __tablename__ = "reports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    owner_id: Mapped[str] = mapped_column(String(64), default=settings.DEFAULT_OWNER, index=True)
    title: Mapped[str] = mapped_column(String(512))
    target_words: Mapped[int] = mapped_column(Integer, default=settings.TARGET_WORDS_DEFAULT)
    user_requirements: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(24), default=ReportStatus.OUTLINE_PENDING.value)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), default=_now)

    chapters: Mapped[list["Chapter"]] = relationship(
        back_populates="report", cascade="all, delete-orphan", order_by="Chapter.chapter_id"
    )


class Chapter(Base):
    __tablename__ = "chapters"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    report_id: Mapped[int] = mapped_column(ForeignKey("reports.id"), index=True)
    chapter_id: Mapped[int] = mapped_column(Integer)            # 章号，从 1 开始
    title: Mapped[str] = mapped_column(String(512))
    key_points: Mapped[str] = mapped_column(Text, default="[]")     # JSON 数组
    data_needed: Mapped[str] = mapped_column(Text, default="[]")    # JSON 数组
    suggested_words: Mapped[int] = mapped_column(Integer, default=0)

    report: Mapped["Report"] = relationship(back_populates="chapters")
