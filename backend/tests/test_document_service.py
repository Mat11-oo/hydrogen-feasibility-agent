"""资料解析与切段的纯函数单测。"""
from app.services.document_service import chunk_text, extract_text, is_scan


def test_chunk_text_splits_into_chunks():
    text = "字" * 2000
    chunks = chunk_text(text, size=800, overlap=100)
    assert len(chunks) == 3  # 800 + 800 + 400
    assert all(len(c) <= 800 for c in chunks)


def test_chunk_text_has_overlap():
    text = "".join(str(i % 10) for i in range(1500))
    chunks = chunk_text(text, size=800, overlap=100)
    # 相邻两段重叠 100 字：前一段末尾与后一段开头一致
    assert chunks[0][-100:] == chunks[1][:100]


def test_chunk_text_empty_returns_empty():
    assert chunk_text("   ", size=800, overlap=100) == []


def test_extract_text_txt(tmp_path):
    f = tmp_path / "a.txt"
    f.write_text("第一段资料内容。", encoding="utf-8")
    text, pages = extract_text("txt", f)
    assert "第一段资料内容" in text
    assert pages == 0


def test_is_scan_detects_low_text_pdf():
    # 30 页只提取到 600 字 → 平均每页 20 字 < 50 → 判扫描件
    assert is_scan("字" * 600, page_count=30) is True
    # 10 页 1000 字 → 平均 100 字/页 → 不是扫描件
    assert is_scan("字" * 1000, page_count=10) is False
