"""大纲：生成 / 查看 / 编辑（F4）。"""
import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.entities import Chapter
from app.schemas.outline import ChapterCreate, ChapterOut, ChapterUpdate, OutlineOut
from app.services import outline_service, report_service
from app.services.model_client import ModelClient, ModelError
from app.services.outline_service import OutlineValidationError

router = APIRouter(prefix="/api/v1/reports/{report_id}/outline", tags=["outline"])


def get_model_client() -> ModelClient:
    return ModelClient()


def _chapter_out(c: Chapter) -> ChapterOut:
    return ChapterOut(
        id=c.id,
        chapter_id=c.chapter_id,
        title=c.title,
        key_points=json.loads(c.key_points or "[]"),
        data_needed=json.loads(c.data_needed or "[]"),
        suggested_words=c.suggested_words,
    )


@router.post("", response_model=OutlineOut)
def generate_outline(
    report_id: int,
    db: Session = Depends(get_db),
    client: ModelClient = Depends(get_model_client),
):
    report = report_service.get_report(db, report_id)
    if report is None:
        raise HTTPException(status_code=404, detail="报告不存在")
    try:
        chapters = outline_service.generate_outline(db, report, client)
    except (ModelError, OutlineValidationError) as exc:
        raise HTTPException(status_code=502, detail=str(exc))
    return OutlineOut(
        report_id=report_id,
        target_words=report.target_words,
        total_words=outline_service.total_words(chapters),
        chapters=[_chapter_out(c) for c in chapters],
    )


@router.get("", response_model=OutlineOut)
def get_outline(report_id: int, db: Session = Depends(get_db)):
    report = report_service.get_report(db, report_id)
    if report is None:
        raise HTTPException(status_code=404, detail="报告不存在")
    chapters = outline_service.get_outline(db, report_id)
    return OutlineOut(
        report_id=report_id,
        target_words=report.target_words,
        total_words=outline_service.total_words(chapters),
        chapters=[_chapter_out(c) for c in chapters],
    )


@router.post("/chapters", response_model=ChapterOut, status_code=201)
def add_chapter(report_id: int, payload: ChapterCreate, db: Session = Depends(get_db)):
    if report_service.get_report(db, report_id) is None:
        raise HTTPException(status_code=404, detail="报告不存在")
    chapter = outline_service.add_chapter(db, report_id, payload)
    return _chapter_out(chapter)


@router.put("/chapters/{chapter_id}", response_model=ChapterOut)
def update_chapter(report_id: int, chapter_id: int, payload: ChapterUpdate, db: Session = Depends(get_db)):
    chapter = db.get(Chapter, chapter_id)
    if chapter is None or chapter.report_id != report_id:
        raise HTTPException(status_code=404, detail="章节不存在")
    chapter = outline_service.update_chapter(db, chapter, payload)
    return _chapter_out(chapter)


@router.delete("/chapters/{chapter_id}", status_code=204)
def delete_chapter(report_id: int, chapter_id: int, db: Session = Depends(get_db)):
    chapter = db.get(Chapter, chapter_id)
    if chapter is None or chapter.report_id != report_id:
        raise HTTPException(status_code=404, detail="章节不存在")
    outline_service.delete_chapter(db, chapter)


@router.post("/chapters/{chapter_id}/move", response_model=OutlineOut)
def move_chapter(report_id: int, chapter_id: int, direction: str = "up", db: Session = Depends(get_db)):
    if direction not in ("up", "down"):
        raise HTTPException(status_code=400, detail="direction 只能是 up 或 down")
    chapter = db.get(Chapter, chapter_id)
    if chapter is None or chapter.report_id != report_id:
        raise HTTPException(status_code=404, detail="章节不存在")
    chapters = outline_service.move_chapter(db, chapter, direction)
    report = report_service.get_report(db, report_id)
    return OutlineOut(
        report_id=report_id,
        target_words=report.target_words,
        total_words=outline_service.total_words(chapters),
        chapters=[_chapter_out(c) for c in chapters],
    )
