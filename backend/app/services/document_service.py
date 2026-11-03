"""资料解析与切段（F1）。只支持 PDF / docx / md / txt；扫描件标「无文字」不入库。"""
import logging
from pathlib import Path

from app.core.config import settings

logger = logging.getLogger(__name__)

SCAN_AVG_CHARS_PER_PAGE = 50  # 平均每页提取不到 50 个字 → 判「无文字」


class DocumentParseError(Exception):
    def __init__(self, reason: str):
        super().__init__(reason)
        self.reason = reason


def extract_text(file_type: str, path: Path) -> tuple[str, int]:
    """按类型提取全文，返回 (文本, 页数)。页数只对 PDF 有意义，其余返回 0。"""
    if file_type == "pdf":
        return _extract_pdf(path)
    if file_type == "docx":
        return _extract_docx(path), 0
    if file_type in ("md", "txt"):
        return _extract_text_file(path), 0
    raise DocumentParseError(f"当前格式不支持，请上传 PDF、Word、Markdown 或 TXT（收到：{file_type}）")


def _extract_pdf(path: Path) -> tuple[str, int]:
    try:
        from pypdf import PdfReader
    except Exception as exc:  # pragma: no cover - 依赖异常兜底
        raise DocumentParseError(f"PDF 解析组件不可用：{exc}") from exc
    try:
        reader = PdfReader(str(path))
        pages = [p.extract_text() or "" for p in reader.pages]
        return "\n".join(pages), len(pages)
    except Exception as exc:
        raise DocumentParseError(f"PDF 解析失败：{exc}") from exc


def _extract_docx(path: Path) -> str:
    try:
        from docx import Document
    except Exception as exc:  # pragma: no cover
        raise DocumentParseError(f"Word 解析组件不可用：{exc}") from exc
    try:
        doc = Document(str(path))
        return "\n".join(p.text for p in doc.paragraphs if p.text.strip())
    except Exception as exc:
        raise DocumentParseError(f"Word 解析失败：{exc}") from exc


def _extract_text_file(path: Path) -> str:
    for enc in ("utf-8", "utf-8-sig", "gb18030"):
        try:
            return path.read_text(encoding=enc)
        except (UnicodeDecodeError, LookupError):
            continue
    raise DocumentParseError("文本文件编码无法识别（尝试了 UTF-8 / GB18030）")


def is_scan(text: str, page_count: int) -> bool:
    """PDF 平均每页提取不到 50 个字 → 判扫描件/图片型，标「无文字」。"""
    if page_count <= 0:
        return False
    return len(text) / page_count < SCAN_AVG_CHARS_PER_PAGE


def chunk_text(text: str, size: int | None = None, overlap: int | None = None) -> list[str]:
    """按约 size 字切段，相邻两段重叠 overlap 字（PRD 第五节参数默认值）。"""
    size = size or settings.CHUNK_SIZE
    overlap = overlap or settings.CHUNK_OVERLAP
    text = text.strip()
    if not text:
        return []
    chunks: list[str] = []
    start = 0
    n = len(text)
    while start < n:
        end = min(start + size, n)
        chunks.append(text[start:end])
        if end >= n:
            break
        start = end - overlap
        if start <= 0:
            start = end  # 防止极端 overlap 造成死循环
    return chunks
