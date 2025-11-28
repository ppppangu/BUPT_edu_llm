# -*- coding: utf-8 -*-
"""FastAPI 应用入口 - API 服务 + 静态前端 + 定时任务"""
import json
import logging
from datetime import datetime
from pathlib import Path
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware

from .config import API_HOST, API_PORT, LOG_LEVEL, PROJECT_DIR, DATA_DIR
from .scheduler import start_scheduler, shutdown_scheduler

# 前端目录
FRONTEND_DIR = PROJECT_DIR / "frontend"

# 配置日志
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    logger.info("AlphaSenti 启动中...")
    start_scheduler()
    logger.info("AlphaSenti 启动完成")
    yield
    logger.info("AlphaSenti 关闭中...")
    shutdown_scheduler()


# 创建应用
app = FastAPI(
    title="AlphaSenti",
    description="股票情绪分析终端 API",
    version="2.1.0",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json"
)

# CORS 配置（允许前端跨域访问）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============== API 路由 ==============

@app.get("/api/health")
async def health():
    """健康检查接口（用于 Docker 健康检查等）"""
    hot_stocks_file = DATA_DIR / "hot_stocks.json"
    data_status = "ok" if hot_stocks_file.exists() else "no_data"

    last_update = None
    if hot_stocks_file.exists():
        try:
            with open(hot_stocks_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            last_update = data.get("updated_at")
        except Exception:
            pass

    return {
        "status": "ok",
        "service": "alpha_sentiment",
        "version": "2.1.0",
        "data_status": data_status,
        "last_update": last_update,
        "timestamp": datetime.now().isoformat()
    }


def _read_json_with_retry(file_path: Path, max_retries: int = 3) -> dict:
    """读取 JSON 文件（带重试，防止刷新时的瞬时读取失败）"""
    import time
    last_error = None
    for attempt in range(max_retries):
        try:
            if not file_path.exists():
                if attempt < max_retries - 1:
                    time.sleep(0.1)  # 短暂等待
                    continue
                return None
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            last_error = e
            if attempt < max_retries - 1:
                time.sleep(0.1)
    logger.warning(f"读取文件失败 {file_path}: {last_error}")
    return None


@app.get("/api/hot_stocks")
async def get_hot_stocks():
    """获取热门股票列表"""
    hot_stocks_file = DATA_DIR / "hot_stocks.json"

    data = _read_json_with_retry(hot_stocks_file)
    if data is None:
        raise HTTPException(status_code=404, detail="数据尚未生成，请稍后重试")

    return data


@app.get("/api/stock/{code}")
async def get_stock_detail(code: str):
    """获取股票详情"""
    # 保留原始代码（包含 SZ/SH 前缀）
    clean_code = code.upper()

    # 尝试直接使用原始代码查找
    stock_file = DATA_DIR / f"stock_{clean_code}.json"

    data = _read_json_with_retry(stock_file)
    if data is None:
        # 如果找不到，尝试去掉前缀后查找（兼容旧格式）
        bare_code = clean_code
        for prefix in ['SZ', 'SH', 'BJ']:
            if bare_code.startswith(prefix):
                bare_code = bare_code[2:]
                break
        bare_code = bare_code.zfill(6)
        stock_file = DATA_DIR / f"stock_{bare_code}.json"
        data = _read_json_with_retry(stock_file)

    if data is None:
        raise HTTPException(status_code=404, detail=f"未找到股票 {code} 的数据")

    return data


@app.post("/api/refresh")
async def refresh_data(background_tasks: BackgroundTasks):
    """手动触发数据刷新（后台执行）"""
    from .services import DataGenerator

    def do_refresh():
        try:
            generator = DataGenerator()
            generator.generate()
            logger.info("手动数据刷新完成")
        except Exception as e:
            logger.error(f"手动数据刷新失败: {e}")

    background_tasks.add_task(do_refresh)
    return {"status": "accepted", "message": "数据刷新任务已提交"}


# ============== 静态文件服务 ==============

# 托管静态数据文件（兼容旧的前端访问方式）
app.mount("/data", StaticFiles(directory=DATA_DIR), name="data")

# 根路径返回前端页面
@app.get("/")
async def root():
    return FileResponse(FRONTEND_DIR / "index.html")


# 旧的健康检查路由（兼容）
@app.get("/health")
async def health_legacy():
    return await health()


def main():
    """主函数"""
    import uvicorn
    uvicorn.run(
        app,
        host=API_HOST,
        port=API_PORT,
        reload=False,
        log_level=LOG_LEVEL.lower()
    )


if __name__ == "__main__":
    main()
