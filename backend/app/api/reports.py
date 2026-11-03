"""报告：创建 / 列表 / 详情（F2、F3）。"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.report import ReportCreate, ReportOut
from app.services import report_service

router = APIRouter(prefix="/api/v1/reports", tags=["reports"])


@router.post("", response_model=ReportOut, status_code=201)
def create_report(payload: ReportCreate, db: Session = Depends(get_db)):
    return report_service.create_report(db, payload)


@router.get("", response_model=list[ReportOut])
def list_reports(db: Session = Depends(get_db)):
    return report_service.list_reports(db)


@router.get("/{report_id}", response_model=ReportOut)
def get_report(report_id: int, db: Session = Depends(get_db)):
    report = report_service.get_report(db, report_id)
    if report is None:
        raise HTTPException(status_code=404, detail="报告不存在")
    return report
