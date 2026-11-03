"""大纲生成与校验（F4）。

程序校验（PRD 第四节）：
1. chapter_id 按顺序从 1 重新编号；
2. suggested_words 加起来不等于目标总字数 → 按比例调平，日志记提醒；
3. 章数不在 8–13 → 自动重新生成一次，仍不对照样显示、提示用户手动增删。
"""
import json
import logging
from pydantic import ValidationError

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.entities import Chapter, Report
from app.schemas.outline import ChapterCreate, ChapterItem, ChapterUpdate
from app.services.model_client import ModelClient, ModelError
from app.services.prompts.outline import build_outline_messages

logger = logging.getLogger(__name__)


class OutlineValidationError(Exception):
    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


def _renumber(chapters: list[dict]) -> list[dict]:
    for i, ch in enumerate(chapters, start=1):
        ch["chapter_id"] = i
    return chapters


def _normalize_words(chapters: list[dict], target_words: int) -> list[dict]:
    """字数调平：按比例缩放各章建议字数，取整，使合计等于目标总字数。"""
    total = sum(ch.get("suggested_words", 0) for ch in chapters)
    if total <= 0:
        # 全为 0 时平分
        per = target_words // len(chapters)
        remainder = target_words - per * len(chapters)
        for i, ch in enumerate(chapters):
            ch["suggested_words"] = per + (1 if i < remainder else 0)
        return chapters
    if total == target_words:
        return chapters
    logger.info("大纲字数调平：%s → %s", total, target_words)
    scaled = [ch["suggested_words"] * target_words // total for ch in chapters]
    diff = target_words - sum(scaled)
    # 余数补到第一项（或从第一项扣）
    for i in range(diff):
        scaled[i] += 1
    for ch, s in zip(chapters, scaled):
        ch["suggested_words"] = max(0, s)
    return chapters


def parse_outline(payload: dict, target_words: int) -> list[dict]:
    """把模型输出解析成合法的大纲列表，做编号与字数校验。"""
    raw = payload.get("full_outline") if isinstance(payload, dict) else None
    if not isinstance(raw, list) or not raw:
        raise OutlineValidationError("大纲为空或格式不对（缺 full_outline 数组）")
    chapters: list[dict] = []
    for i, item in enumerate(raw, start=1):
        if not isinstance(item, dict):
            raise OutlineValidationError("大纲章节必须是对象")
        try:
            chapter = ChapterItem.model_validate({**item, "chapter_id": i})
        except ValidationError as exc:
            raise OutlineValidationError("大纲章节格式不符合要求，请重新生成") from exc
        chapters.append(chapter.model_dump())
    if not chapters:
        raise OutlineValidationError("大纲里没有可用的章节")
    _renumber(chapters)
    _normalize_words(chapters, target_words)
    return chapters


def generate_outline(db: Session, report: Report, client: ModelClient) -> list[Chapter]:
    """调模型生成大纲，最多自动重新生成一次（章数不在 8–13 时）。"""
    messages = build_outline_messages(report.title, report.target_words, report.user_requirements)
    last_err: Exception | None = None
    for attempt in range(2):  # 首次 + 章数不对再试一次
        try:
            payload = client.chat_json(messages)
            chapters_data = parse_outline(payload, report.target_words)
        except (ModelError, OutlineValidationError) as exc:
            last_err = exc
            continue
        if settings.OUTLINE_MIN_CHAPTERS <= len(chapters_data) <= settings.OUTLINE_MAX_CHAPTERS:
            return _store_chapters(db, report, chapters_data)
        last_err = OutlineValidationError(
            f"章数不在 {settings.OUTLINE_MIN_CHAPTERS}–{settings.OUTLINE_MAX_CHAPTERS}（得到 {len(chapters_data)}）"
        )
        logger.warning("大纲章数不对，重新生成：%s", last_err)
    # 两次都失败：抛错给上层，由路由返回统一错误
    raise OutlineValidationError(f"大纲生成失败：{last_err}")


def _store_chapters(db: Session, report: Report, chapters_data: list[dict]) -> list[Chapter]:
    # 覆盖旧大纲（重新生成）
    for old in report.chapters:
        db.delete(old)
    db.flush()
    out: list[Chapter] = []
    for ch in chapters_data:
        c = Chapter(
            report_id=report.id,
            chapter_id=ch["chapter_id"],
            title=ch["title"],
            key_points=json.dumps(ch["key_points"], ensure_ascii=False),
            data_needed=json.dumps(ch["data_needed"], ensure_ascii=False),
            suggested_words=ch["suggested_words"],
        )
        db.add(c)
        out.append(c)
    db.commit()
    return out


def get_outline(db: Session, report_id: int) -> list[Chapter]:
    stmt = select(Chapter).where(Chapter.report_id == report_id).order_by(Chapter.chapter_id)
    return list(db.scalars(stmt))


def total_words(chapters: list[Chapter]) -> int:
    return sum(c.suggested_words for c in chapters)


def add_chapter(db: Session, report_id: int, payload: ChapterCreate) -> Chapter:
    chapters = get_outline(db, report_id)
    new_id = (max((c.chapter_id for c in chapters), default=0)) + 1
    c = Chapter(
        report_id=report_id,
        chapter_id=new_id,
        title=payload.title.strip(),
        key_points=json.dumps(payload.key_points, ensure_ascii=False),
        data_needed=json.dumps(payload.data_needed, ensure_ascii=False),
        suggested_words=payload.suggested_words,
    )
    db.add(c)
    db.commit()
    db.refresh(c)
    return c


def update_chapter(db: Session, chapter: Chapter, payload: ChapterUpdate) -> Chapter:
    if payload.title is not None:
        chapter.title = payload.title.strip()
    if payload.key_points is not None:
        chapter.key_points = json.dumps(payload.key_points, ensure_ascii=False)
    if payload.data_needed is not None:
        chapter.data_needed = json.dumps(payload.data_needed, ensure_ascii=False)
    if payload.suggested_words is not None:
        chapter.suggested_words = payload.suggested_words
    db.commit()
    db.refresh(chapter)
    return chapter


def delete_chapter(db: Session, chapter: Chapter) -> None:
    report_id = chapter.report_id
    db.delete(chapter)
    db.commit()
    # 重新编号，保持章号连续
    for i, c in enumerate(get_outline(db, report_id), start=1):
        c.chapter_id = i
    db.commit()


def move_chapter(db: Session, chapter: Chapter, direction: str) -> list[Chapter]:
    """上移/下移一章，交换 chapter_id。"""
    chapters = get_outline(db, chapter.report_id)
    idx = next((i for i, c in enumerate(chapters) if c.id == chapter.id), None)
    if idx is None:
        return chapters
    target = idx - 1 if direction == "up" else idx + 1
    if not (0 <= target < len(chapters)):
        return chapters  # 已到顶/底，不动
    chapters[idx], chapters[target] = chapters[target], chapters[idx]
    for i, c in enumerate(chapters, start=1):
        c.chapter_id = i
    db.commit()
    return get_outline(db, chapter.report_id)
