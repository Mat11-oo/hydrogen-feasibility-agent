"""模型调用封装：OpenAI 兼容接口 + 结构化 JSON 输出 + 超时/失败/有限重试。

设计要点（手册第九节之 3、AGENTS.md 底线 4）：
- 模型名、base_url、超时从配置读，不硬编码。
- 解析失败走有限重试（含 SDK 初始化失败兜底），仍失败抛统一错误。
- 只记录元信息，不记完整用户文档和密钥。
"""
import json
import logging
import re
import time

from openai import OpenAI

from app.core.config import settings

logger = logging.getLogger(__name__)


class ModelError(Exception):
    """模型调用失败（含 SDK 初始化失败、超时、输出不是合法 JSON）。"""

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


def _lenient_parse_json(text: str) -> dict:
    """宽容解析：去掉 Markdown 代码块围栏，再找第一个 JSON 对象。"""
    t = text.strip()
    # 去掉 ```json ... ``` 或 ``` ... ``` 围栏
    t = re.sub(r"^```[a-zA-Z]*\s*", "", t)
    t = re.sub(r"\s*```$", "", t)
    try:
        return json.loads(t)
    except json.JSONDecodeError:
        pass
    # 找第一个 { 到最后一个 }
    start = t.find("{")
    end = t.rfind("}")
    if start != -1 and end > start:
        try:
            return json.loads(t[start : end + 1])
        except json.JSONDecodeError:
            pass
    raise ModelError("模型输出不是合法 JSON")


class ModelClient:
    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        model_name: str | None = None,
        timeout: float | None = None,
    ):
        self.api_key = api_key if api_key is not None else settings.MODEL_API_KEY
        self.base_url = base_url or settings.MODEL_BASE_URL
        self.model_name = model_name or settings.MODEL_NAME
        self.timeout = timeout if timeout is not None else settings.MODEL_TIMEOUT_SECONDS
        self.calls: list[dict] = []
        # 无 Key 时保留占位客户端；真正调用会在 chat_json 里报出清晰错误
        try:
            self._client = OpenAI(api_key=self.api_key, base_url=self.base_url, timeout=self.timeout, max_retries=0)
        except Exception as exc:  # SDK 初始化失败兜底
            logger.warning("模型 SDK 初始化失败 type=%s", type(exc).__name__)
            self._client = None

    def chat_json(self, messages: list[dict]) -> dict:
        """调模型并返回解析后的 JSON 对象。失败自动重试，最多 settings.MODEL_MAX_RETRIES 次。"""
        if self._client is None or not self.api_key:
            raise ModelError("未配置模型 API Key（backend/.env 的 MODEL_API_KEY）")
        last_err: Exception | None = None
        for attempt in range(settings.MODEL_MAX_RETRIES + 1):
            started = time.time()
            try:
                resp = self._client.chat.completions.create(
                    model=self.model_name,
                    messages=messages,
                    temperature=0.3,
                )
                content = (resp.choices[0].message.content or "").strip()
                call = {
                    "request_id": getattr(resp, "id", "-") or "-",
                    "input_tokens": getattr(resp.usage, "prompt_tokens", "-") if resp.usage else "-",
                    "output_tokens": getattr(resp.usage, "completion_tokens", "-") if resp.usage else "-",
                    "elapsed": time.time() - started,
                    "retry": attempt,
                    "result": "失败",
                }
                self.calls.append(call)
                logger.info(
                    "模型调用成功 model=%s attempt=%d elapsed=%.1fs",
                    self.model_name, attempt + 1, time.time() - started,
                )
                payload = _lenient_parse_json(content)
                if not isinstance(payload, dict):
                    raise ModelError("模型输出必须是 JSON 对象")
                call["result"] = "已解析"
                return payload
            except ModelError as exc:
                last_err = exc
            except Exception as exc:  # 超时、限流、网络等
                last_err = exc
                self.calls.append({"request_id": "-", "input_tokens": "-", "output_tokens": "-", "elapsed": time.time() - started, "retry": attempt, "result": "失败"})
                logger.warning("模型调用失败 attempt=%d type=%s", attempt + 1, type(exc).__name__)
            if attempt < settings.MODEL_MAX_RETRIES:
                time.sleep(1.5 * (attempt + 1))  # 间隔逐次加长
        raise ModelError(f"模型调用失败（已重试 {settings.MODEL_MAX_RETRIES} 次），请检查配置或稍后重试")
