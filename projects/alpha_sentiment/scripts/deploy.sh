#!/bin/bash
# Alpha Sentiment 部署脚本（自包含版本）
set -e

# ============================================
# 日志函数（自包含，不依赖外部库）
# ============================================
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info()    { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warn()    { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error()   { echo -e "${RED}[ERROR]${NC} $1"; }

# ============================================
# 路径设置
# ============================================
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PROJECT_NAME="alpha_sentiment"

log_info "=========================================="
log_info "$PROJECT_NAME 部署脚本"
log_info "=========================================="

cd "$PROJECT_DIR"

# ============================================
# 1. 加载环境变量
# ============================================
if [ -f .env ]; then
    log_info "加载 .env 文件"
    set -a && source .env && set +a
else
    log_warn "未找到 .env 文件，使用默认配置"
fi

# 默认配置
ALPHA_SENTIMENT_HOST=${ALPHA_SENTIMENT_HOST:-127.0.0.1}
ALPHA_SENTIMENT_PORT=${ALPHA_SENTIMENT_PORT:-5001}

log_info "服务地址: http://$ALPHA_SENTIMENT_HOST:$ALPHA_SENTIMENT_PORT"
log_info "API 文档: http://$ALPHA_SENTIMENT_HOST:$ALPHA_SENTIMENT_PORT/api/docs"
log_info "健康检查: http://$ALPHA_SENTIMENT_HOST:$ALPHA_SENTIMENT_PORT/api/health"

# ============================================
# 2. 检查依赖
# ============================================
if ! command -v uv &> /dev/null; then
    log_error "未找到 uv，请先安装: curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi

# ============================================
# 3. 安装依赖
# ============================================
log_info "安装依赖..."
uv sync

# ============================================
# 4. 启动服务
# ============================================
log_info "启动服务..."
uv run gunicorn -w 2 -k uvicorn.workers.UvicornWorker \
    -b $ALPHA_SENTIMENT_HOST:$ALPHA_SENTIMENT_PORT \
    --access-logfile - \
    --error-logfile - \
    backend.main:app

log_success "=========================================="
log_success "$PROJECT_NAME 部署完成"
log_success "=========================================="
