# -*- coding: utf-8 -*-
"""FastAPI 应用入口"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware

from backend.config import FRONTEND_DIR, HOST, PORT, LOG_LEVEL
from backend.services.news_service import news_service
from backend.scheduler import start_scheduler, stop_scheduler

logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    logger.info("Solar News Crawler 启动中...")
    start_scheduler()
    yield
    stop_scheduler()


app = FastAPI(
    title="Solar News Crawler",
    version="0.3.0",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url=None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==================== API 路由 ====================

@app.get("/api/health")
async def health():
    return {"status": "ok"}


@app.get("/api/news")
async def get_news(
    start_date: str = None,
    end_date: str = None,
    keyword: str = "",
    source: str = ""
):
    """国内新闻"""
    return news_service.get_news(
        start_date=start_date,
        end_date=end_date,
        keyword=keyword.strip() or None,
        source=source.strip() or None
    )


@app.get("/api/news/stats")
async def get_news_stats():
    return news_service.get_news_stats()


@app.get("/api/international")
async def get_international_news(
    start_date: str = None,
    end_date: str = None,
    keyword: str = "",
    source: str = ""
):
    """国际新闻"""
    return news_service.get_international_news(
        start_date=start_date,
        end_date=end_date,
        keyword=keyword.strip() or None,
        source=source.strip() or None
    )


@app.get("/api/international/stats")
async def get_international_stats():
    return news_service.get_international_stats()


@app.get("/api/summary/{news_type}")
async def get_ai_summary(news_type: str):
    """AI总结 (domestic/international)"""
    return news_service.get_ai_summary(news_type)


# ==================== 页面路由 ====================

@app.get("/")
async def index():
    return FileResponse(FRONTEND_DIR / "index.html")


@app.get("/news_search")
async def news_search_page():
    return FileResponse(FRONTEND_DIR / "news_search.html")


@app.get("/translated_news")
async def translated_news_page():
    return FileResponse(FRONTEND_DIR / "translated_news.html")


# ==================== 静态文件 ====================

app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=HOST, port=PORT, log_level=LOG_LEVEL.lower())
