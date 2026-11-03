"""FastAPI 入口：路由、静态验收界面、统一错误结构、启动建表。"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.api import documents, outline, reports
from app.core.config import BACKEND_DIR
from app.core.database import Base, engine

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title="可研报告生成 Agent", version="0.1.0", lifespan=lifespan)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={"error": {"code": "validation_error", "message": "请求参数不符合要求，请检查必填项、类型及字数范围"}},
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": f"http_{exc.status_code}", "message": str(exc.detail)}},
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logging.getLogger(__name__).exception("未处理异常：%s", exc)
    return JSONResponse(
        status_code=500,
        content={"error": {"code": "internal_error", "message": "服务器内部错误，请稍后重试"}},
    )


app.include_router(documents.router)
app.include_router(reports.router)
app.include_router(outline.router)

# 临时验收界面（阶段 2-1，阶段 3 开始时废弃）
app.mount("/", StaticFiles(directory=str(BACKEND_DIR / "static"), html=True), name="static")
