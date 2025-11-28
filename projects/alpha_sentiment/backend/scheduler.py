# -*- coding: utf-8 -*-
"""定时任务调度器（带告警机制）"""
import asyncio
import json
import logging
import traceback
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from typing import Optional
import httpx

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from .services import DataGenerator
from .config import DATA_DIR, ALERT_WEBHOOK_URL, ALERT_ENABLED

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()
executor = ThreadPoolExecutor(max_workers=1)


class AlertService:
    """告警服务"""

    @staticmethod
    async def send_alert(
        status: str,
        message: str,
        details: Optional[dict] = None
    ) -> bool:
        """
        发送告警通知

        Args:
            status: 状态 (success/error/warning)
            message: 告警消息
            details: 详细信息

        Returns:
            是否发送成功
        """
        if not ALERT_ENABLED:
            logger.debug("告警未启用，跳过发送")
            return True

        try:
            payload = {
                "msgtype": "markdown",
                "markdown": {
                    "title": f"AlphaSenti 数据刷新{'成功' if status == 'success' else '失败'}",
                    "text": AlertService._format_message(status, message, details)
                }
            }

            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(ALERT_WEBHOOK_URL, json=payload)
                if response.status_code == 200:
                    logger.info(f"告警发送成功: {message}")
                    return True
                else:
                    logger.warning(f"告警发送失败: {response.status_code}")
                    return False

        except Exception as e:
            logger.error(f"告警发送异常: {e}")
            return False

    @staticmethod
    def _format_message(status: str, message: str, details: Optional[dict]) -> str:
        """格式化告警消息（Markdown）"""
        icon = "✅" if status == "success" else "❌" if status == "error" else "⚠️"
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        text = f"## {icon} AlphaSenti 数据刷新通知\n\n"
        text += f"**状态**: {status.upper()}\n\n"
        text += f"**消息**: {message}\n\n"
        text += f"**时间**: {timestamp}\n\n"

        if details:
            text += "**详情**:\n"
            for key, value in details.items():
                text += f"- {key}: {value}\n"

        return text


def generate_static_data() -> tuple[bool, Optional[str]]:
    """
    生成静态数据文件（供定时任务调用）

    Returns:
        (成功标志, 错误信息)
    """
    try:
        generator = DataGenerator()
        success = generator.generate()
        return success, None
    except Exception as e:
        error_msg = f"{type(e).__name__}: {str(e)}"
        logger.error(f"数据生成异常: {error_msg}")
        logger.debug(traceback.format_exc())
        return False, error_msg


async def refresh_data_task():
    """异步包装，在线程中运行同步的 generate 方法（带告警）"""
    start_time = datetime.now()
    logger.info("开始执行定时数据刷新任务...")

    try:
        loop = asyncio.get_event_loop()
        success, error_msg = await loop.run_in_executor(executor, generate_static_data)

        elapsed = (datetime.now() - start_time).total_seconds()

        if success:
            # 读取生成的数据统计
            hot_stocks_file = DATA_DIR / "hot_stocks.json"
            stats = {}
            if hot_stocks_file.exists():
                try:
                    with open(hot_stocks_file, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    stats = {
                        "总股票数": data.get("total_stocks", 0),
                        "成功数": data.get("success_count", 0),
                        "失败数": data.get("failed_count", 0),
                        "耗时": f"{elapsed:.1f}秒"
                    }
                except Exception:
                    pass

            logger.info(f"数据刷新成功，耗时 {elapsed:.1f} 秒")
            await AlertService.send_alert(
                status="success",
                message="每日数据刷新完成",
                details=stats
            )
        else:
            logger.error(f"数据刷新失败: {error_msg}")
            await AlertService.send_alert(
                status="error",
                message=f"每日数据刷新失败: {error_msg}",
                details={"耗时": f"{elapsed:.1f}秒"}
            )

    except Exception as e:
        elapsed = (datetime.now() - start_time).total_seconds()
        error_msg = f"{type(e).__name__}: {str(e)}"
        logger.error(f"刷新任务异常: {error_msg}")
        logger.debug(traceback.format_exc())

        await AlertService.send_alert(
            status="error",
            message=f"刷新任务异常: {error_msg}",
            details={"耗时": f"{elapsed:.1f}秒"}
        )


def setup_scheduler():
    """配置定时任务 - 每天收盘后刷新一次"""
    # 每天 15:30 收盘后刷新数据
    scheduler.add_job(
        refresh_data_task,
        CronTrigger(hour=15, minute=30),
        id="daily_refresh",
        name="每日数据刷新",
        replace_existing=True
    )

    # 检查是否需要立即刷新
    hot_stocks_file = DATA_DIR / "hot_stocks.json"
    need_refresh = False

    if not hot_stocks_file.exists():
        need_refresh = True
        logger.info("无缓存数据，需要刷新")
    else:
        try:
            with open(hot_stocks_file, "r", encoding="utf-8") as f:
                cached = json.load(f)
            updated_at = cached.get("updated_at", "")
            if updated_at:
                cached_date = datetime.fromisoformat(updated_at).date()
                if cached_date < datetime.now().date():
                    need_refresh = True
                    logger.info(f"数据已过期（{cached_date}），需要刷新")
        except Exception as e:
            need_refresh = True
            logger.warning(f"读取缓存失败: {e}")

    if need_refresh:
        scheduler.add_job(
            refresh_data_task,
            "date",
            id="initial_refresh",
            name="初始数据刷新"
        )

    logger.info("定时任务配置完成")
    if ALERT_ENABLED:
        logger.info(f"告警已启用，Webhook: {ALERT_WEBHOOK_URL[:30]}...")
    else:
        logger.info("告警未启用（未配置 ALPHA_SENTIMENT_ALERT_WEBHOOK）")


def start_scheduler():
    """启动调度器"""
    setup_scheduler()
    scheduler.start()
    logger.info("调度器已启动")


def shutdown_scheduler():
    """关闭调度器"""
    scheduler.shutdown()
    logger.info("调度器已关闭")
