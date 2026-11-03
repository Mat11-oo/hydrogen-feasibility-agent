"""接口测试：报告创建/列表、资料上传、大纲生成（mock 模型）。"""
import json

from app.api.outline import get_model_client
from app.main import app


class FakeModelClient:
    """假模型：返回固定大纲，不联网。"""

    def __init__(self, payload):
        self.payload = payload

    def chat_json(self, messages):
        return self.payload


def _install_fake_outline(chapters):
    payload = {"full_outline": chapters}
    app.dependency_overrides[get_model_client] = lambda: FakeModelClient(payload)


def _clear_overrides():
    app.dependency_overrides.clear()


def test_create_report_ok(client):
    r = client.post("/api/v1/reports", json={"title": "测试报告", "target_words": 12000, "user_requirements": ""})
    assert r.status_code == 201
    data = r.json()
    assert data["title"] == "测试报告"
    assert data["status"] == "outline_pending"


def test_create_report_rejects_too_many_words(client):
    r = client.post("/api/v1/reports", json={"title": "x", "target_words": 20000})
    assert r.status_code == 422  # Pydantic 校验：超过 18000


def test_create_report_requires_title(client):
    r = client.post("/api/v1/reports", json={"title": "", "target_words": 1000})
    assert r.status_code == 422


def test_list_reports(client):
    client.post("/api/v1/reports", json={"title": "A", "target_words": 1000})
    client.post("/api/v1/reports", json={"title": "B", "target_words": 2000})
    r = client.get("/api/v1/reports")
    assert r.status_code == 200
    assert len(r.json()) == 2


def test_upload_txt_document(client):
    files = {"file": ("资料.txt", "这是一段测试资料内容，用于验证上传和切段。", "text/plain")}
    r = client.post("/api/v1/documents", files=files)
    assert r.status_code == 201
    data = r.json()
    assert data["status"] == "available"
    assert data["chunk_count"] >= 1


def test_upload_rejects_unsupported_ext(client):
    files = {"file": ("资料.exe", b"\x00\x01", "application/octet-stream")}
    r = client.post("/api/v1/documents", files=files)
    assert r.status_code == 400
    assert r.json()["error"]["message"]


def _eight_chapters():
    return [
        {"chapter_id": i, "title": f"第{i}章", "key_points": ["p"], "data_needed": ["总投资"], "suggested_words": 100}
        for i in range(1, 9)
    ]


def test_generate_outline_with_fake_model(client):
    _install_fake_outline(_eight_chapters())
    try:
        rep = client.post("/api/v1/reports", json={"title": "大纲测试", "target_words": 800}).json()
        r = client.post(f"/api/v1/reports/{rep['id']}/outline")
        assert r.status_code == 200
        data = r.json()
        assert len(data["chapters"]) == 8
        assert data["chapters"][0]["chapter_id"] == 1
        assert data["total_words"] == 800
    finally:
        _clear_overrides()


def test_generate_outline_chapter_count_retry(client):
    """章数不在 8–13 时自动重新生成一次（假模型第二次给合法章数）。"""
    calls = {"n": 0}

    class FlakyClient:
        def chat_json(self, messages):
            calls["n"] += 1
            if calls["n"] == 1:
                return {"full_outline": [{"chapter_id": 1, "title": "x", "key_points": [], "data_needed": [], "suggested_words": 100}]}
            return {"full_outline": [
                {"chapter_id": i, "title": f"第{i}章", "key_points": [], "data_needed": [], "suggested_words": 100}
                for i in range(1, 9)
            ]}

    app.dependency_overrides[get_model_client] = lambda: FlakyClient()
    try:
        rep = client.post("/api/v1/reports", json={"title": "重试测试", "target_words": 800}).json()
        r = client.post(f"/api/v1/reports/{rep['id']}/outline")
        assert r.status_code == 200
        assert len(r.json()["chapters"]) == 8
        assert calls["n"] == 2
    finally:
        _clear_overrides()


def test_edit_outline_chapter(client):
    _install_fake_outline(_eight_chapters())
    try:
        rep = client.post("/api/v1/reports", json={"title": "编辑测试", "target_words": 800}).json()
        client.post(f"/api/v1/reports/{rep['id']}/outline")
        outline = client.get(f"/api/v1/reports/{rep['id']}/outline").json()
        cid = outline["chapters"][0]["id"]
        r = client.put(
            f"/api/v1/reports/{rep['id']}/outline/chapters/{cid}",
            json={"title": "新标题", "suggested_words": 90},
        )
        assert r.status_code == 200
        assert r.json()["title"] == "新标题"
    finally:
        _clear_overrides()


def test_error_structure_is_unified(client):
    r = client.get("/api/v1/reports/99999")
    assert r.status_code == 404
    body = r.json()
    assert "error" in body
    assert "code" in body["error"] and "message" in body["error"]


def test_validation_error_is_unified_without_echoing_input(client):
    response = client.post('/api/v1/reports', json={'title': 'private-input', 'target_words': 20000})
    assert response.status_code == 422
    assert response.json()['error']['code'] == 'validation_error'
    assert 'private-input' not in response.text


def test_invalid_model_output_returns_controlled_error_and_preserves_old_outline(client):
    _install_fake_outline(_eight_chapters())
    rep = client.post('/api/v1/reports', json={'title': 'structure-test', 'target_words': 800}).json()
    url = f"/api/v1/reports/{rep['id']}/outline"
    original = client.post(url).json()
    _install_fake_outline([{'title': 'x', 'key_points': None, 'suggested_words': 100}])
    response = client.post(url)
    assert response.status_code == 502
    assert response.json()['error']['message']
    assert client.get(url).json() == original
