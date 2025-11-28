#!/bin/bash
# Solar News Crawler 部署脚本

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$PROJECT_DIR"

# 读取端口配置
PORT="${SOLAR_NEWS_PORT:-5000}"
WORKERS="${SOLAR_NEWS_WORKERS:-4}"
HOST="${SOLAR_NEWS_HOST:-127.0.0.1}"

echo "[solar_news_crawler] 启动服务 - http://$HOST:$PORT"

# 使用 uv 运行 gunicorn
exec uv run gunicorn \
    --bind "$HOST:$PORT" \
    --workers "$WORKERS" \
    --access-logfile - \
    --error-logfile - \
    "backend.main:create_app()"
