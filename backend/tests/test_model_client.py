"""模型失败时不回显上游异常。"""
import pytest

from app.services.model_client import ModelClient, ModelError
from app.core.config import settings


def test_upstream_error_does_not_expose_details(monkeypatch, caplog):
    def broken(**kwargs):
        raise RuntimeError('private-provider-detail')
    model = ModelClient(api_key='fake-for-test')
    monkeypatch.setattr(model._client.chat.completions, 'create', broken)
    monkeypatch.setattr(settings, 'MODEL_MAX_RETRIES', 0)
    with pytest.raises(ModelError) as exc:
        model.chat_json([])
    assert 'private-provider-detail' not in str(exc.value)
    assert 'private-provider-detail' not in caplog.text
