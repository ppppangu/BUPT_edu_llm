#!/bin/bash
# Stop all services for BUPT EDU LLM Platform
# Usage: ./stop_all.sh

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

log_info "=========================================="
log_info "BUPT EDU LLM Platform 停止脚本"
log_info "=========================================="

if [ ! -d "$PID_DIR" ]; then
    log_warn "PID 目录不存在: $PID_DIR"
    exit 0
fi

# Stop all services by reading PID files
for pid_file in "$PID_DIR"/*.pid; do
    if [ -f "$pid_file" ]; then
        service_name=$(basename "$pid_file" .pid)
        pid=$(cat "$pid_file")

        log_info "停止 $service_name (PID: $pid)..."

        if ps -p $pid > /dev/null 2>&1; then
            kill $pid 2>/dev/null || true
            sleep 1

            # Force kill if still running
            if ps -p $pid > /dev/null 2>&1; then
                log_warn "强制终止 $service_name..."
                kill -9 $pid 2>/dev/null || true
            fi

            log_success "$service_name 已停止"
        else
            log_warn "$service_name 未在运行"
        fi

        rm "$pid_file"
    fi
done

log_info "=========================================="
log_success "所有服务已停止"
log_info "=========================================="
