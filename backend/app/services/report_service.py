"""报告业务：创建 / 列表 / 详情（F2、F3）。数据读写集中在 service 层，不散在路由。"""
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.entities import Report, ReportStatus
from app.schemas.report import ReportCreate


def create_report(db: Session, payload: ReportCreate) -> Report:
    report = Report(
        owner_id=settings.DEFAULT_OWNER,
        title=payload.title.strip(),
        target_words=payload.target_words,
        user_requirements=payload.user_requirements.strip(),
        status=ReportStatus.OUTLINE_PENDING.value,
    )
    db.add(report)
    db.commit()
    db.refresh(report)
    return report


def list_reports(db: Session) -> list[Report]:
    stmt = select(Report).where(Report.owner_id == settings.DEFAULT_OWNER).order_by(Report.created_at.desc())
    return list(db.scalars(stmt))


def get_report(db: Session, report_id: int) -> Report | None:
    return db.get(Report, report_id)
