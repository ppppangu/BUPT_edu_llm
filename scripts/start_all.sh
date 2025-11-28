#!/bin/bash
# Start all services for BUPT EDU LLM Platform
# Usage: ./start_all.sh

set -e

# ============================================
# 日志函数（自包含）
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
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
PID_DIR="$PROJECT_ROOT/.pids"

# Trap Ctrl+C to stop all services
cleanup() {
    log_warn "收到中断信号，正在停止所有服务..."
    "$SCRIPT_DIR/stop_all.sh"
    exit 0
}
trap cleanup SIGINT SIGTERM

log_info "=========================================="
log_info "BUPT EDU LLM Platform 启动脚本"
log_info "=========================================="

# Create PID directory
mkdir -p "$PID_DIR"

# 项目列表（静态配置）
PROJECTS="solar_news_crawler alpha_sentiment"

log_info "启动项目: $PROJECTS"

for project_id in $PROJECTS; do
    # 新路径：projects/<project_id>/scripts/deploy.sh
    deploy_script="$PROJECT_ROOT/projects/$project_id/scripts/deploy.sh"

    if [ -f "$deploy_script" ]; then
        log_info "启动 $project_id..."
        "$deploy_script" &
        echo $! > "$PID_DIR/$project_id.pid"
        log_success "$project_id 已启动 (PID: $!)"
    else
        log_warn "未找到部署脚本: $deploy_script"
    fi
done

log_info "=========================================="
log_success "所有服务已启动"
log_info "PID 文件保存在: $PID_DIR"
log_info "按 Ctrl+C 停止所有服务"
log_info "=========================================="

# Wait for all background processes
wait
