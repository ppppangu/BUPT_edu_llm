"""配置文件"""
import os
from pathlib import Path
from dotenv import load_dotenv

# 基础路径
BASE_DIR = Path(__file__).parent
PROJECT_DIR = BASE_DIR.parent

# 加载 .env 文件（系统环境变量优先，.env 作为备用）
load_dotenv(PROJECT_DIR / ".env")

# 静态数据输出目录（与 backend、frontend 同级）
DATA_DIR = PROJECT_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

# LLM 配置（统一命名，两个项目共用）
LLM_API_KEY = os.getenv("LLM_API_KEY", "")
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "https://api.deepseek.com")
LLM_MODEL = os.getenv("LLM_MODEL", "deepseek-chat")

# 数据配置
MAX_HOT_STOCKS = int(os.getenv("ALPHA_SENTIMENT_MAX_HOT_STOCKS", "20"))

# 服务配置
API_HOST = os.getenv("ALPHA_SENTIMENT_HOST", "127.0.0.1")
API_PORT = int(os.getenv("ALPHA_SENTIMENT_PORT", "5001"))

# 日志配置
LOG_LEVEL = os.getenv("ALPHA_SENTIMENT_LOG_LEVEL", "INFO")

# 重试配置（统一管理）
MAX_RETRIES = int(os.getenv("ALPHA_SENTIMENT_MAX_RETRIES", "5"))
RETRY_DELAY = float(os.getenv("ALPHA_SENTIMENT_RETRY_DELAY", "2.0"))

# 告警配置（可选）
ALERT_WEBHOOK_URL = os.getenv("ALPHA_SENTIMENT_ALERT_WEBHOOK", "")
ALERT_ENABLED = bool(ALERT_WEBHOOK_URL)
