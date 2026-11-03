"""集中配置：只从这里读环境变量，代码不硬编码密钥和模型名。"""
import os
from pathlib import Path

from dotenv import load_dotenv

# backend/ 目录（config.py 位于 backend/app/core/）
BACKEND_DIR = Path(__file__).resolve().parents[2]
# 产品文件夹根目录（backend/ 的上一级）
PROJECT_ROOT = BACKEND_DIR.parent

# 读取 backend/.env（不存在也不报错；真实 Key 由产品经理写进 backend/.env，已 gitignore）
load_dotenv(BACKEND_DIR / ".env")
load_dotenv(PROJECT_ROOT / ".env")


def _data_dir() -> Path:
    """数据目录：restart-check 时用 RESTART_CHECK_DIR 指向临时目录，平时用产品 data/。"""
    override = os.environ.get("RESTART_CHECK_DIR") or os.environ.get("DATA_DIR")
    if override:
        return Path(override)
    return PROJECT_ROOT / "data"


class Settings:
    # 数据与文件
    DATA_DIR: Path = _data_dir()
    UPLOAD_DIR: Path = DATA_DIR / "uploads"
    DATABASE_URL: str = os.environ.get("DATABASE_URL", f"sqlite:///{DATA_DIR / 'app.db'}")

    # 模型（走 OpenAI 兼容接口；默认指向 DeepSeek，与决策台账 D4 一致）
    MODEL_API_KEY: str = os.environ.get("MODEL_API_KEY", "")
    MODEL_BASE_URL: str = os.environ.get("MODEL_BASE_URL", "https://api.deepseek.com")
    MODEL_NAME: str = os.environ.get("MODEL_NAME", "deepseek-chat")
    REVIEW_MODEL_NAME: str = os.environ.get("REVIEW_MODEL_NAME", "deepseek-chat")
    MODEL_TIMEOUT_SECONDS: float = float(os.environ.get("MODEL_TIMEOUT_SECONDS", "120"))
    MODEL_MAX_RETRIES: int = int(os.environ.get("MODEL_MAX_RETRIES", "3"))

    # 业务参数（PRD 第五节参数默认值）
    TARGET_WORDS_DEFAULT: int = 12000
    TARGET_WORDS_MAX: int = 18000
    CHAPTER_WORDS_MAX_FACTOR: float = 1.1
    CHUNK_SIZE: int = 800
    CHUNK_OVERLAP: int = 100
    OUTLINE_MIN_CHAPTERS: int = 8
    OUTLINE_MAX_CHAPTERS: int = 13
    MAX_FILE_SIZE_MB: int = 100

    # 归属字段：阶段 2 暂不登录，写固定默认归属（AGENTS.md 底线 7 / 手册第九节第 2 条）
    DEFAULT_OWNER: str = "default"

    # 允许上传的扩展名与真实类型白名单（PRD 第五节）
    ALLOWED_EXTENSIONS: tuple = (".pdf", ".docx", ".md", ".txt")


settings = Settings()

# 确保数据目录存在
settings.DATA_DIR.mkdir(parents=True, exist_ok=True)
settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
