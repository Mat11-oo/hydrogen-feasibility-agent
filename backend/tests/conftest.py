"""测试夹具：把数据库/数据目录指到临时位置，再导入 app，避免污染真实数据。"""
import os
import tempfile

_tmp = tempfile.mkdtemp(prefix="kesan-test-")
os.environ["DATABASE_URL"] = f"sqlite:///{_tmp}/test.db"
os.environ["DATA_DIR"] = _tmp
os.environ["RESTART_CHECK_DIR"] = _tmp
os.environ["MODEL_API_KEY"] = "fake-for-test"  # 短于 20 字符，不会被 verify.sh 密钥扫描误判

import pytest
from fastapi.testclient import TestClient

from app.core.database import Base, engine
from app.main import app


@pytest.fixture()
def client():
    # 每个测试前重置数据库，避免用例之间互相污染
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    app.dependency_overrides.clear()
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
