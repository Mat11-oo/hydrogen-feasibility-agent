"""资料上传 / 列表（F1）。上传校验：扩展名、真实类型、大小、安全文件名。"""
import logging
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.models.entities import Document, DocumentChunk, DocumentStatus
from app.schemas.document import DocumentOut
from app.services import document_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/documents", tags=["documents"])


def _safe_ext(filename: str) -> str:
    return Path(filename).suffix.lower()


def _detect_real_type(filename: str, content: bytes) -> str | None:
    """用文件头/内容判断真实类型，防伪装扩展名。"""
    ext = _safe_ext(filename)
    if ext == ".pdf":
        return "pdf" if content.startswith(b"%PDF") else None
    if ext == ".docx":
        return "docx" if content.startswith(b"PK") else None
    if ext in (".md", ".txt"):
        # 文本类：无 NUL 字节即视为文本（具体编码解析交给 document_service，支持 utf-8/gb18030）
        return ext[1:] if b"\x00" not in content[:4096] else None
    return None


@router.post("", response_model=DocumentOut, status_code=201)
async def upload_document(file: UploadFile = File(...), db: Session = Depends(get_db)):
    original_name = file.filename or ""
    ext = _safe_ext(original_name)
    if ext not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"当前格式不支持，请上传 PDF、Word、Markdown 或 TXT")

    content = await file.read()
    if len(content) > settings.MAX_FILE_SIZE_MB * 1024 * 1024:
        raise HTTPException(status_code=400, detail=f"上传失败，最大支持 {settings.MAX_FILE_SIZE_MB}M 文件")

    real_type = _detect_real_type(original_name, content)
    if real_type is None:
        raise HTTPException(status_code=400, detail="文件内容与扩展名不符，请检查文件是否损坏或伪装")

    # 安全文件名：uuid + 原扩展名，避免路径遍历和同名覆盖
    stored_name = f"{uuid.uuid4().hex}{ext}"
    stored_path = settings.UPLOAD_DIR / stored_name
    stored_path.write_bytes(content)

    # 解析
    doc = Document(
        owner_id=settings.DEFAULT_OWNER,
        filename=stored_name,
        original_name=original_name,
        file_type=real_type,
        status=DocumentStatus.AVAILABLE.value,
        stored_path=str(stored_path),
    )
    try:
        text, page_count = document_service.extract_text(real_type, stored_path)
        if document_service.is_scan(text, page_count):
            doc.status = DocumentStatus.NO_TEXT.value
            doc.error_reason = "扫描件或图片型 PDF，请上传文字版"
        else:
            chunks = document_service.chunk_text(text)
            if not chunks:
                doc.status = DocumentStatus.NO_TEXT.value
                doc.error_reason = "文件里没有可检索的文字"
            else:
                doc.chunk_count = len(chunks)
                for i, c in enumerate(chunks):
                    doc.chunks.append(DocumentChunk(chunk_index=i, content=c))
    except document_service.DocumentParseError as exc:
        doc.status = DocumentStatus.FAILED.value
        doc.error_reason = exc.reason

    db.add(doc)
    db.commit()
    db.refresh(doc)
    return doc


@router.get("", response_model=list[DocumentOut])
def list_documents(db: Session = Depends(get_db)):
    stmt = select(Document).where(Document.owner_id == settings.DEFAULT_OWNER).order_by(Document.created_at.desc())
    return list(db.scalars(stmt))
