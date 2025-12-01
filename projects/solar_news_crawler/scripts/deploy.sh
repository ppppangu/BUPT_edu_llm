#!/bin/bash
# Solar News Crawler 部署脚本

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$PROJECT_DIR"

# 读取配置
PORT="${SOLAR_NEWS_PORT:-5000}"
HOST="${SOLAR_NEWS_HOST:-127.0.0.1}"
WORKERS="${SOLAR_NEWS_WORKERS:-2}"

echo "[solar_news_crawler] 启动服务 - http://$HOST:$PORT"

# 使用 uvicorn 启动
exec uv run uvicorn backend.main:app \
    --host "$HOST" \
    --port "$PORT" \
    --workers "$WORKERS" \
    --log-level info
