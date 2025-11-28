"""配置文件"""
import os
from pathlib import Path
from dotenv import load_dotenv

# 基础路径
BASE_DIR = Path(__file__).parent
PROJECT_DIR = BASE_DIR.parent

# 加载 .env 文件（override=True 确保覆盖系统环境变量）
load_dotenv(PROJECT_DIR / ".env", override=True)

# 静态数据输出目录（与 backend、frontend 同级）
DATA_DIR = PROJECT_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

# 环境变量配置（带 ALPHA_SENTIMENT_ 前缀防止冲突）
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")

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
