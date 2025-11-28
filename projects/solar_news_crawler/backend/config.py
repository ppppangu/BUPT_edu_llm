# -*- coding: utf-8 -*-
"""配置管理模块"""
import os
from pathlib import Path

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
CRAWLERS_DIR = PROJECT_ROOT / "crawlers"
FRONTEND_DIR = PROJECT_ROOT / "frontend"

# 确保数据目录存在
DATA_DIR.mkdir(exist_ok=True)

# 服务配置
HOST = os.getenv("SOLAR_NEWS_HOST", "127.0.0.1")
PORT = int(os.getenv("SOLAR_NEWS_PORT", "5000"))
WORKERS = int(os.getenv("SOLAR_NEWS_WORKERS", "4"))
LOG_LEVEL = os.getenv("SOLAR_NEWS_LOG_LEVEL", "INFO")

# LLM 配置（统一命名，两个项目共用）
LLM_API_KEY = os.getenv("LLM_API_KEY", "")
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "")
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-3.5-turbo")
LLM_ENABLED = bool(LLM_BASE_URL and LLM_API_KEY)

# 定时任务配置
SCHEDULER_HOUR = int(os.getenv("SCHEDULER_HOUR", "2"))  # 凌晨2点执行
SCHEDULER_MINUTE = int(os.getenv("SCHEDULER_MINUTE", "0"))
