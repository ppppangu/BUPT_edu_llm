# -*- coding: utf-8 -*-
"""定时任务调度器"""
import glob
import json
import os
from datetime import datetime
from typing import Optional

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from backend.config import DATA_DIR, SCHEDULER_HOUR, SCHEDULER_MINUTE
from backend.services.crawler_service import crawler_service
from backend.services.translator_service import translator_service
from backend.services.ai_service import ai_service


def find_latest_file(pattern: str) -> Optional[str]:
    """查找最新文件"""
    files = glob.glob(str(DATA_DIR / pattern))
    if not files:
        return None
    files.sort(key=os.path.getmtime, reverse=True)
    return files[0]


def daily_crawl_task():
    """每日爬虫任务"""
    print(f"\n{'='*60}")
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 开始执行每日爬虫任务")
    print(f"{'='*60}\n")

    try:
        # 1. 运行所有爬虫
        print("Step 1: 运行爬虫...")
        crawler_results = crawler_service.run_all_crawlers(timeout_per_crawler=600)
        print(f"爬虫完成: {crawler_results['total_success']}/4 成功, "
              f"获取 {crawler_results['total_count']} 条数据")

        # 2. 运行翻译
        print("\nStep 2: 翻译国际新闻...")
        try:
            translator_output = translator_service.merge_and_save_translations()
            if translator_output:
                print(f"翻译完成: {translator_output}")
        except Exception as e:
            print(f"翻译失败: {e}")
            translator_output = None

        # 3. 生成 AI 总结
        print("\nStep 3: 生成 AI 总结...")

        # 国内新闻总结
        combined_file = crawler_results['results'].get('combined', {}).get('file')
        if combined_file and os.path.exists(combined_file):
            try:
                with open(combined_file, 'r', encoding='utf-8') as f:
                    domestic_data = json.load(f)
                result = ai_service.run_summary(domestic_data, 'domestic', 'summary_domestic.json')
                if result.get('success'):
                    print("国内新闻 AI 总结生成成功")
                else:
                    print(f"国内新闻 AI 总结失败: {result.get('error')}")
            except Exception as e:
                print(f"国内新闻 AI 总结失败: {e}")

        # 国际新闻总结
        if translator_output and os.path.exists(translator_output):
            try:
                with open(translator_output, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                international_data = data.get('news_list', [])
                result = ai_service.run_summary(international_data, 'international', 'summary_international.json')
                if result.get('success'):
                    print("国际新闻 AI 总结生成成功")
                else:
                    print(f"国际新闻 AI 总结失败: {result.get('error')}")
            except Exception as e:
                print(f"国际新闻 AI 总结失败: {e}")

        print(f"\n{'='*60}")
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 每日爬虫任务完成")
        print(f"{'='*60}\n")

    except Exception as e:
        print(f"每日爬虫任务执行出错: {e}")


def generate_static_data():
    """
    单独运行数据生成任务（供部署脚本调用）
    """
    daily_crawl_task()


# 全局调度器实例
scheduler = BackgroundScheduler()


def start_scheduler():
    """启动调度器"""
    if scheduler.running:
        print("调度器已在运行")
        return

    # 添加每日任务
    scheduler.add_job(
        daily_crawl_task,
        CronTrigger(hour=SCHEDULER_HOUR, minute=SCHEDULER_MINUTE),
        id='daily_crawl',
        name='每日爬虫任务',
        replace_existing=True
    )

    scheduler.start()
    print(f"调度器已启动，每日 {SCHEDULER_HOUR:02d}:{SCHEDULER_MINUTE:02d} 执行爬虫任务")


def stop_scheduler():
    """停止调度器"""
    if scheduler.running:
        scheduler.shutdown()
        print("调度器已停止")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "now":
        # 立即执行一次
        daily_crawl_task()
    else:
        # 启动调度器
        print("启动定时调度器...")
        print(f"每日执行时间: {SCHEDULER_HOUR:02d}:{SCHEDULER_MINUTE:02d}")
        print("按 Ctrl+C 停止")

        start_scheduler()

        try:
            import time
            while True:
                time.sleep(60)
        except KeyboardInterrupt:
            stop_scheduler()
            print("调度器已退出")
