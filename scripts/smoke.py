"""阶段2-1真实冒烟：实际 API → 模型 → 持久化 → GET 回读，隔离业务数据。"""
import os
import sys
import tempfile
from datetime import datetime
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent
BACKEND = PROJECT / "backend"
sys.path.insert(0, str(BACKEND))

from dotenv import load_dotenv


def main():
    load_dotenv(BACKEND / ".env")
    if not os.environ.get("MODEL_API_KEY", "").strip():
        print("未配置 MODEL_API_KEY，真实冒烟待验（不写记录）。")
        return 1
    stage = next((a for a in sys.argv[1:] if a.startswith("阶段")), "阶段2-1")
    if stage not in {"阶段2-1", "阶段3-1"}:
        print("此脚本当前仅覆盖阶段2-1与阶段3-1复用的大纲模型链路。")
        return 1
    with tempfile.TemporaryDirectory(prefix="feasibility-smoke-") as tmp:
        os.environ["DATA_DIR"] = tmp
        os.environ["RESTART_CHECK_DIR"] = tmp
        os.environ["DATABASE_URL"] = f"sqlite:///{tmp}/smoke.db"
        from fastapi.testclient import TestClient
        from app.api.outline import get_model_client
        from app.core.config import settings
        from app.core.database import engine
        from app.main import app
        from app.services.model_client import ModelClient
        from app.services.outline_service import parse_outline

        class ObservedClient(ModelClient):
            def chat_json(self, messages):
                payload = super().chat_json(messages)
                try:
                    chapters = parse_outline(payload, settings.TARGET_WORDS_DEFAULT)
                    valid = settings.OUTLINE_MIN_CHAPTERS <= len(chapters) <= settings.OUTLINE_MAX_CHAPTERS
                    self.calls[-1]["result"] = "通过" if valid else "瑕疵待打分"
                except Exception:
                    self.calls[-1]["result"] = "失败"
                    raise
                return payload

        model = ObservedClient()
        app.dependency_overrides[get_model_client] = lambda: model
        success = False
        try:
            with TestClient(app, raise_server_exceptions=False) as api:
                created = api.post("/api/v1/reports", json={
                    "title": "攀枝花市钒钛高新区制氢加氢一体化示范项目（一期）",
                    "target_words": settings.TARGET_WORDS_DEFAULT,
                })
                assert created.status_code == 201
                report_id = created.json()["id"]
                generated = api.post(f"/api/v1/reports/{report_id}/outline")
                assert generated.status_code == 200
                outline = generated.json()
                assert settings.OUTLINE_MIN_CHAPTERS <= len(outline["chapters"]) <= settings.OUTLINE_MAX_CHAPTERS
                assert outline["total_words"] == settings.TARGET_WORDS_DEFAULT
                saved = api.get(f"/api/v1/reports/{report_id}/outline")
                assert saved.status_code == 200 and saved.json() == outline
                success = True
                print(f"真实冒烟通过：实际 API 生成 {len(outline['chapters'])} 章，保存后 GET 回读一致。")
        except Exception as exc:
            print(f"真实冒烟失败（{type(exc).__name__}），未输出模型原文或错误详情。")
        finally:
            app.dependency_overrides.clear()
            engine.dispose()
            record = PROJECT / "docs" / "evidence" / stage / "冒烟记录.md"
            record.parent.mkdir(parents=True, exist_ok=True)
            if not record.exists():
                record.write_text(
                    "# 冒烟记录（冒烟脚本自动写入，不得手填）\n"
                    f"- 产品：{PROJECT.name}\n- 阶段：{stage}\n"
                    f"- 模型：{settings.MODEL_BASE_URL} / {settings.MODEL_NAME}\n"
                    f"- 写入时间：{datetime.now():%Y-%m-%d %H:%M:%S}\n\n"
                    "| 时间 | 链路 | 请求 ID | 输入 token | 输出 token | 首字耗时 | 总耗时 | 结构校验 | 重试次数 | 结果 |\n"
                    "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |\n", encoding="utf-8")
            with record.open("a", encoding="utf-8") as f:
                for i, call in enumerate(model.calls):
                    result = call["result"]
                    if result == "已解析" or (i == len(model.calls) - 1 and not success):
                        result = "失败"
                    structure = "首测合规" if result == "通过" and i == 0 else "重试合规" if result == "通过" else "失败"
                    f.write(f"| {datetime.now():%Y-%m-%d %H:%M:%S} | 生成大纲→保存→回读 | {call['request_id']} | {call['input_tokens']} | {call['output_tokens']} | - | {call['elapsed']:.1f}s | {structure} | {i} | {result} |\n")
        return 0 if success else 1


if __name__ == "__main__":
    raise SystemExit(main())
